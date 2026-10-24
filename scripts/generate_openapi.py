import os
import sys
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

def main():
    schema = app.openapi()
    schema["openapi"] = "3.1.0"
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "openapi.yaml"))
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, sort_keys=False, allow_unicode=True)
    print(f"Generated OpenAPI 3.1.0 specification at {out_path}")

if __name__ == "__main__":
    main()
