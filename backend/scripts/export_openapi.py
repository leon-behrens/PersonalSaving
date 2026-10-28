import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from personalsaving.app import create_app


def main() -> None:
    app: FastAPI = create_app()
    schema: dict[str, Any] = app.openapi()

    # Deployment URLs vary; exclude servers from the committed API contract.
    schema.pop("servers", None)
    document: str = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    output_path: Path = Path(__file__).resolve().parents[1] / "openapi.json"
    output_path.write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
