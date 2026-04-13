import pandas as pd

from pipeline import transform_products


def test_transform_products_normalizes_expected_fields() -> None:
    frame = pd.DataFrame(
        [
            {
                "raw_title": " Test Phone ",
                "raw_category": " Phones ",
                "raw_price": "USD 199",
                "raw_region": "us-south",
            }
        ]
    )

    transformed = transform_products(frame)
    record = transformed.to_dict(orient="records")[0]

    assert record["title"] == "Test Phone"
    assert record["category"] == "smartphones"
    assert record["currency"] == "USD"
    assert record["price"] == 199.0
    assert record["region"] == "us_south"
    assert record["catalog_ready"] is True
