#!/usr/bin/env python3
"""The old prescribed benchmark lifecycle is retained only as historical data."""
import json

def validate_fixture(*args, **kwargs):
    return ["legacy prescribed-route fixture retired; use selected-model and dispatcher behavior tests"]

if __name__ == "__main__":
    print(json.dumps({"status":"retired", "failures":validate_fixture()}))
    raise SystemExit(2)
