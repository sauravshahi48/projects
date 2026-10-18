FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY docassist ./docassist
RUN pip install --no-cache-dir . && useradd --create-home appuser && mkdir /data && chown appuser:appuser /data
USER appuser
ENV DOCASSIST_DATA_DIR=/data
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "docassist.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
