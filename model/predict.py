from __future__ import annotations

import argparse
import json
import sys

from inference import LifeLensPredictor


def main() -> int:
    parser = argparse.ArgumentParser(description="Predict disease from symptoms.")
    parser.add_argument(
        "--symptoms",
        required=True,
        help="Comma-separated symptoms such as fever,cough,headache",
    )
    parser.add_argument("--limit", type=int, default=3, help="Number of top predictions to return.")
    args = parser.parse_args()

    symptoms = [item.strip() for item in args.symptoms.split(",") if item.strip()]

    try:
        predictor = LifeLensPredictor()
        payload = predictor.predict(symptoms, top_k=args.limit)
    except Exception as error:
        print(json.dumps({"error": str(error)}))
        return 1

    sys.stdout.write(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
