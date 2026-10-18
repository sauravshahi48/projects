"use strict";
const $ = (id) => document.getElementById(id);
let documents = [];
let busy = false;
let lastResult = null;

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) {
    const detail = typeof result.detail === "string" ? result.detail : "The request could not be completed.";
    throw new Error(detail);
  }
  return result;
}

function feedback(message = "", error = false) {
  $("feedback").textContent = message;
  $("feedback").classList.toggle("error", error);
}

function setBusy(value) {
  busy = value;
  $("ask-button").disabled = value;
  $("demo-button").disabled = value;
  $("file-input").disabled = value;
  $("scope").disabled = value;
  document.querySelectorAll(".remove-document, .suggestions button").forEach((b) => b.disabled = value);
}

function clearResult() {
  lastResult = null;
  $("answer-panel").hidden = true;
  $("how-it-works").hidden = false;
  feedback();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function refreshDocuments() {
  documents = (await api("/api/documents")).documents;
  $("document-count").textContent = documents.length;
  $("empty-library").hidden = documents.length > 0;
  const list = $("document-list");
  list.replaceChildren();
  const selected = $("scope").value;
  $("scope").replaceChildren(new Option("All documents", "all"));
  for (const doc of documents) {
    $("scope").add(new Option(doc.name, doc.id));
    const row = element("div", "document-item");
    row.append(element("span", "file-icon", doc.name.split(".").pop().toUpperCase().slice(0,3)));
    const detail = element("div", "file-detail");
    const link = element("a", "", doc.name);
    link.href = doc.url; link.target = "_blank"; link.rel = "noopener";
    detail.append(link, element("small", "", `${doc.pages} ${doc.pages === 1 ? "page" : "pages"} · ${doc.chunks} passages`));
    const remove = element("button", "remove-document", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `Remove ${doc.name}`);
    remove.disabled = busy;
    remove.addEventListener("click", async () => {
      if (busy) return;
      setBusy(true);
      try {
        await api(`/api/documents/${doc.id}`, {method:"DELETE"});
        clearResult();
        await refreshDocuments();
        feedback(`Removed ${doc.name}.`);
      } catch (error) { feedback(error.message, true); }
      finally { setBusy(false); }
    });
    row.append(detail, remove); list.append(row);
  }
  if (documents.some((d) => d.id === selected)) $("scope").value = selected;
}

async function upload(files) {
  if (busy || !files.length) return;
  setBusy(true); clearResult();
  $("upload-status").textContent = "Reading and indexing documents…";
  try {
    const data = new FormData();
    for (const file of files) data.append("files", file);
    const result = await api("/api/documents", {method:"POST", body:data});
    await refreshDocuments();
    const added = result.documents.filter((d) => !d.duplicate).length;
    const duplicate = result.documents.filter((d) => d.duplicate).length;
    const messages = [`${added} document${added === 1 ? "" : "s"} added.`];
    if (duplicate) messages.push(`${duplicate} already in your knowledge base.`);
    if (result.errors.length) messages.push(...result.errors.map((e) => `${e.filename}: ${e.error}`));
    $("upload-status").textContent = messages.join(" ");
  } catch (error) { $("upload-status").textContent = error.message; }
  finally { $("file-input").value = ""; setBusy(false); }
}

$("file-input").addEventListener("change", (event) => upload(Array.from(event.target.files)));
const dropzone = $("dropzone");
dropzone.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && !busy) {
    event.preventDefault(); $("file-input").click();
  }
});
for (const name of ["dragenter", "dragover"]) dropzone.addEventListener(name, (event) => {
  event.preventDefault(); if (!busy) dropzone.classList.add("dragover");
});
for (const name of ["dragleave", "drop"]) dropzone.addEventListener(name, (event) => {
  event.preventDefault(); dropzone.classList.remove("dragover");
});
dropzone.addEventListener("drop", (event) => upload(Array.from(event.dataTransfer.files)));

$("demo-button").addEventListener("click", async () => {
  if (busy) return;
  setBusy(true); clearResult();
  $("upload-status").textContent = "Loading fictional company policies…";
  try {
    await api("/api/demo", {method:"POST"});
    await refreshDocuments();
    $("upload-status").textContent = "Sample policies are ready. Try one of the questions.";
  } catch (error) { $("upload-status").textContent = error.message; }
  finally { setBusy(false); }
});

function showResult(result) {
  lastResult = result;
  $("answer-panel").hidden = false;
  $("how-it-works").hidden = true;
  $("asked-question").textContent = result.question;
  $("answer-text").textContent = result.answer;
  $("result-type").textContent = result.status === "answered" ? "Answer with verified source references" : result.status === "not_found" ? "Insufficient evidence" : "Retrieved source passages · no generated answer";
  $("latency").textContent = `${Math.round(result.latency_ms)} ms`;
  $("result-notice").hidden = !result.notice;
  $("result-notice").textContent = result.notice || "";
  $("sources-heading").hidden = result.sources.length === 0;
  $("sources-count").textContent = result.sources.length;
  $("retrieval-label").textContent = `${result.retrieval === "hybrid" ? "FAISS + TF-IDF hybrid" : "TF-IDF lexical"} search · ${result.mode === "llm" ? "Generated answer" : "Source evidence"}`;
  const grid = $("sources"); grid.replaceChildren();
  for (const source of result.sources) {
    const card = element("article", "source-card");
    const title = element("div", "source-title");
    title.append(element("span", "citation-label", source.label), element("span", "source-name", `${source.filename} · p. ${source.page}`));
    const bottom = element("div", "source-bottom");
    bottom.append(element("span", "", `Similarity ${source.score.toFixed(3)}`));
    const link = element("a", "", "Open source page ↗");
    link.href = source.url; link.target = "_blank"; link.rel = "noopener";
    bottom.append(link);
    card.append(title, element("p", "source-excerpt", source.excerpt), bottom); grid.append(card);
  }
  $("answer-panel").scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block:"nearest"});
}

$("question-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const question = $("question").value.trim();
  if (question.length < 3) { feedback("Enter a question with at least three characters.", true); return; }
  if (!documents.length) { feedback("Add a document or load the sample policies first.", true); return; }
  setBusy(true);
  $("answer-panel").hidden = true;
  feedback("Searching your documents…"); $("feedback").classList.add("loading");
  try {
    const scope = $("scope").value;
    const result = await api("/api/ask", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question, document_ids:scope === "all" ? null : [scope]})});
    showResult(result); feedback();
  } catch (error) { feedback(error.message, true); }
  finally { $("feedback").classList.remove("loading"); setBusy(false); }
});
$("question").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("question-form").requestSubmit(); }
});
document.querySelectorAll("[data-question]").forEach((button) => button.addEventListener("click", () => {
  $("question").value = button.dataset.question; $("question").focus();
  if (documents.length) $("question-form").requestSubmit();
  else feedback("Load the sample documents to explore this example.");
}));
$("scope").addEventListener("change", clearResult);
$("download-answer").addEventListener("click", () => {
  if (!lastResult) return;
  const result = lastResult;
  const lines = ["SourceDesk result", "", `Question: ${result.question}`, `Status: ${result.status}`, `Mode: ${result.mode}`, "", result.answer, ""];
  for (const s of result.sources) lines.push(`[${s.label}] ${s.filename}, page ${s.page}`, s.excerpt, "");
  if (result.notice) lines.push(result.notice);
  const url = URL.createObjectURL(new Blob([lines.join("\n")], {type:"text/plain;charset=utf-8"}));
  const link = element("a"); link.href=url; link.download="sourcedesk-result.txt"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

(async function init() {
  try {
    const health = await api("/api/health");
    $("mode-badge").replaceChildren(element("i"), document.createTextNode(health.answer_mode === "llm" ? "LLM answers enabled" : "Local evidence mode"));
    if (health.sends_passages_to_provider) {
      $("privacy-title").textContent = "LLM answers enabled";
      $("privacy-description").textContent = "Questions and retrieved passages are sent to your configured model provider.";
    }
    $("engine-label").textContent = health.answer_mode === "llm" ? "LangChain generation · Page citations" : health.retrieval === "hybrid" ? "Local semantic + lexical retrieval" : "Offline retrieval · No API key needed";
    await refreshDocuments();
  } catch (error) { feedback(`Could not connect: ${error.message}`, true); $("mode-badge").textContent="Connection unavailable"; }
})();
