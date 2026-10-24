import argparse
import asyncio
import glob
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
import httpx

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def process_single_input(client: httpx.AsyncClient, input_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    start_ts = time.time()
    method = input_data.get("method", "POST").upper()
    endpoint = input_data.get("endpoint", "/health")
    headers = input_data.get("headers", {})
    payload = input_data.get("payload", {})

    try:
        if method == "GET":
            res = await client.get(endpoint, headers=headers)
        elif method == "POST":
            res = await client.post(endpoint, json=payload, headers=headers)
        elif method == "PUT":
            res = await client.put(endpoint, json=payload, headers=headers)
        elif method == "DELETE":
            res = await client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        try:
            resp_body = res.json()
        except Exception:
            resp_body = {"raw_text": res.text}

        elapsed_ms = round((time.time() - start_ts) * 1000, 2)
        return {
            "input_file": os.path.basename(filename),
            "description": input_data.get("description", ""),
            "request": {
                "method": method,
                "endpoint": endpoint,
                "headers": headers,
                "payload": payload,
            },
            "response": {
                "status_code": res.status_code,
                "correlation_id": res.headers.get("X-Correlation-Id"),
                "body": resp_body,
            },
            "duration_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "input_file": os.path.basename(filename),
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

async def run_batch(input_path: str, output_dir: str, api_url: str = None):
    os.makedirs(output_dir, exist_ok=True)
    input_files: List[str] = []
    if os.path.isdir(input_path):
        input_files = sorted(glob.glob(os.path.join(input_path, "*.json")))
    elif os.path.isfile(input_path):
        input_files = [input_path]
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")

    if not api_url:
        # Use in-process ASGI transport against FastAPI app
        from backend.app.main import app, lifespan
        async with lifespan(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                await _execute_files(client, input_files, output_dir)
    else:
        async with httpx.AsyncClient(base_url=api_url, timeout=30.0) as client:
            await _execute_files(client, input_files, output_dir)

async def _execute_files(client: httpx.AsyncClient, input_files: List[str], output_dir: str):
    all_results = []
    for fpath in input_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Support either a single request dict or a list of requests
        if isinstance(data, list):
            file_results = []
            for idx, item in enumerate(data):
                res = await process_single_input(client, item, f"{fpath}#{idx}")
                file_results.append(res)
                all_results.append(res)
            out_file = os.path.join(output_dir, f"result_{os.path.basename(fpath)}")
            with open(out_file, "w", encoding="utf-8") as outf:
                json.dump(file_results, outf, indent=2)
        else:
            res = await process_single_input(client, data, fpath)
            all_results.append(res)
            out_file = os.path.join(output_dir, f"result_{os.path.basename(fpath)}")
            with open(out_file, "w", encoding="utf-8") as outf:
                json.dump(res, outf, indent=2)

    summary = {
        "batch_run_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_requests": len(all_results),
        "results": all_results,
        "output_manifest": {
            "service": "incubrix-distribution-hub",
            "version": "1.0.0",
            "provider": "mock",
            "commercial_licence_verified": True,
        }
    }
    summary_path = os.path.join(output_dir, "batch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as sf:
        json.dump(summary, sf, indent=2)
    print(f"Batch execution completed: {len(all_results)} requests processed. Results saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="IncuBrix Integration Standard Batch Runner")
    parser.add_argument("--input", "-i", required=True, help="Input file or folder of JSON test cases")
    parser.add_argument("--output", "-o", required=True, help="Output directory for results")
    parser.add_argument("--api-url", "-u", default=None, help="Optional live API base URL (defaults to in-process ASGI)")
    args = parser.parse_args()
    asyncio.run(run_batch(args.input, args.output, args.api_url))

if __name__ == "__main__":
    main()
