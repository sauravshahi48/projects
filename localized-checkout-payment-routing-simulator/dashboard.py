from __future__ import annotations

from flask import Flask, jsonify

from api.db import initialize_database
from api.service import fetch_rules


app = Flask(__name__)
initialize_database()


@app.get("/")
def index():
    return jsonify(
        {
            "regions": {
                "IN": fetch_rules("IN", "INR"),
                "DE": fetch_rules("DE", "EUR"),
                "US": fetch_rules("US", "USD"),
            }
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
