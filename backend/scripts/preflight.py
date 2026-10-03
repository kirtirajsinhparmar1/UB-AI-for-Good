"""Check that the API package imports in the current environment."""

import importlib.util
import sys


def main() -> int:
    missing = [
        package
        for package in ("fastapi", "multipart", "uvicorn")
        if importlib.util.find_spec(package) is None
    ]
    if missing:
        print("Missing backend dependencies: " + ", ".join(missing), file=sys.stderr)
        return 1

    from app.api.main import app

    print("API imports successfully; model inference is not ready.")
    return 0 if app else 1


if __name__ == "__main__":
    raise SystemExit(main())
