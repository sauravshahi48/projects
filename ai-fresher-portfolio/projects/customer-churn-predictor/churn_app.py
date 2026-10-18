from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from churn_model import FEATURES, predict_customer, train_model
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).parent


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    call_failures: int = Field(ge=0, le=1000)
    complaints: Literal[0, 1]
    subscription_months: int = Field(ge=0, le=240)
    charge_band: int = Field(ge=0, le=9)
    seconds_of_use: int = Field(ge=0, le=10_000_000)
    call_frequency: int = Field(ge=0, le=1_000_000)
    sms_frequency: int = Field(ge=0, le=1_000_000)
    distinct_numbers: int = Field(ge=0, le=100_000)
    tariff_plan: Literal[1, 2]


def create_app():
    bundle = train_model()
    app = FastAPI(title="Customer Churn Predictor", version="1.0.0")

    @app.get("/")
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/metrics")
    def metrics():
        return bundle.report

    @app.get("/api/schema")
    def schema():
        return {"fields": bundle.schema, "example": bundle.example}

    @app.get("/api/example.csv")
    def example_csv():
        return Response(
            pd.DataFrame([bundle.example]).to_csv(index=False),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="example_customers.csv"'},
        )

    @app.post("/api/predict")
    def predict(customer: Customer):
        return predict_customer(bundle, customer.model_dump())

    @app.post("/api/batch")
    async def batch(file: Annotated[UploadFile, File(...)]):
        try:
            data = await file.read(1_000_001)
        finally:
            await file.close()
        if len(data) > 1_000_000:
            raise HTTPException(400, "Upload a CSV smaller than 1 MB.")
        try:
            frame = pd.read_csv(BytesIO(data))
            if not 1 <= len(frame) <= 2000:
                raise ValueError("Use between 1 and 2000 customer rows.")
            if set(frame.columns) != set(FEATURES):
                raise ValueError(
                    "Use the nine columns in the example CSV, without a churn target column."
                )
            records = [
                Customer.model_validate(row).model_dump() for row in frame.to_dict(orient="records")
            ]
        except (
            ValueError,
            ValidationError,
            pd.errors.ParserError,
            UnicodeError,
        ) as exc:
            raise HTTPException(
                400, "Invalid CSV. Check the example format and numeric field ranges."
            ) from exc
        output = pd.DataFrame(records, columns=list(FEATURES))
        probabilities = bundle.model.predict_proba(output)[:, 1]
        output["churn_score"] = probabilities.round(4)
        output["above_threshold"] = probabilities >= bundle.report["threshold"]
        return Response(
            output.to_csv(index=False),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="churn_scores.csv"'},
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("churn_app:create_app", factory=True, host="127.0.0.1", port=8002)
