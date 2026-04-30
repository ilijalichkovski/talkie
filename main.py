"""Run Talkie on the roman-numerals problem and score its solution.

Usage:
    uv run main.py            # run once (uses server if available, else loads model)
    uv run main.py --serve    # start the model server (load once, serve forever)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBLEM_DIR = ROOT / "problem"
RESULTS_DIR = ROOT / "results"
TEACH_FILE = ROOT / "teach.md"

MODEL_NAME = "talkie-1930-13b-it"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5193


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_prompt() -> str:
    teacher_instruction = load_text(TEACH_FILE)
    introduction = load_text(PROBLEM_DIR / "introduction.md")
    instructions = load_text(PROBLEM_DIR / "instructions.md")

    prompt = (
        f"{teacher_instruction}"
        # f"{teacher_instruction}\n\n"
        # f"--- Problem Introduction ---\n{introduction}\n\n"
        # f"--- Problem Instructions ---\n{instructions}\n\n"
    )
    return prompt


def extract_code(raw_output: str) -> str:
    """Pull Python code out of the model's response.

    Tries fenced code blocks first, then falls back to the full output.
    """
    fenced = re.search(r"```(?:python)?\s*\n(.+?)```", raw_output, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    return raw_output.strip()


# ---------------------------------------------------------------------------
# Server mode: load model once, serve over HTTP
# ---------------------------------------------------------------------------

def start_server() -> None:
    """Load the model and serve generation requests over HTTP."""
    import http.server
    import socketserver

    sys.path.insert(0, str(ROOT / "src"))
    from talkie import Talkie

    print("Loading model…", file=sys.stderr)
    model = Talkie(MODEL_NAME)
    print(f"Model ready. Serving on {SERVER_HOST}:{SERVER_PORT}", file=sys.stderr)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            prompt = body["prompt"]
            temperature = body.get("temperature", 0.7)
            max_tokens = body.get("max_tokens", 1024)
            stream = body.get("stream", False)

            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                full_text = []
                for token in model.stream(
                    prompt, temperature=temperature, max_tokens=max_tokens
                ):
                    full_text.append(token)
                    chunk = json.dumps({"token": token}) + "\n"
                    self.wfile.write(chunk.encode())
                    self.wfile.flush()
                done = json.dumps({"done": True, "text": "".join(full_text)}) + "\n"
                self.wfile.write(done.encode())
                self.wfile.flush()
            else:
                result = model.generate(
                    prompt, temperature=temperature, max_tokens=max_tokens
                )
                response = json.dumps({"text": result.text})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response.encode())

        def log_message(self, format, *args):
            print(f"[server] {args[0]}", file=sys.stderr)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((SERVER_HOST, SERVER_PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.", file=sys.stderr)


def _server_is_running() -> bool:
    """Check if the model server is reachable."""
    import urllib.request
    try:
        req = urllib.request.Request(
            f"http://{SERVER_HOST}:{SERVER_PORT}/",
            data=json.dumps({"prompt": "", "max_tokens": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def run_talkie_via_server(prompt: str) -> str:
    """Send a prompt to the running model server."""
    import urllib.request
    body = json.dumps({"prompt": prompt, "temperature": 0.7, "max_tokens": 1024})
    req = urllib.request.Request(
        f"http://{SERVER_HOST}:{SERVER_PORT}/",
        data=body.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=300)
    data = json.loads(resp.read())
    return data["text"]


def run_talkie_local(prompt: str) -> str:
    """Load the model in-process and generate (slow cold start)."""
    sys.path.insert(0, str(ROOT / "src"))
    from talkie import Talkie

    print("Loading model…", file=sys.stderr)
    model = Talkie(MODEL_NAME)
    print("Generating…", file=sys.stderr)
    result = model.generate(prompt, temperature=0.7, max_tokens=1024)
    return result.text


def run_talkie(prompt: str) -> str:
    """Run inference — via server if available, otherwise local."""
    if _server_is_running():
        print("Using model server.", file=sys.stderr)
        return run_talkie_via_server(prompt)
    else:
        print("No server found, loading model locally (slow)…", file=sys.stderr)
        return run_talkie_local(prompt)


def run_tests(code: str) -> dict:
    """Write the code to a temp dir alongside the test file and run pytest."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        (tmp_path / "roman_numerals.py").write_text(code, encoding="utf-8")

        test_src = (PROBLEM_DIR / "roman_numerals_test.py").read_text(encoding="utf-8")
        (tmp_path / "roman_numerals_test.py").write_text(test_src, encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "roman_numerals_test.py"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=30,
        )

    passed = len(re.findall(r" PASSED", proc.stdout))
    failed = len(re.findall(r" FAILED", proc.stdout))
    errors = len(re.findall(r" ERROR", proc.stdout))
    total = passed + failed + errors

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "score": f"{passed}/{total}" if total else "0/0",
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
    }


def save_result(
    teacher_instruction: str,
    raw_output: str,
    extracted_code: str,
    test_result: dict,
) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = RESULTS_DIR / f"run_{timestamp}.json"

    record = {
        "timestamp": timestamp,
        "model": MODEL_NAME,
        "teacher_instruction": teacher_instruction,
        "talkie_full_output": raw_output,
        "extracted_code": extracted_code,
        "score": test_result["score"],
        "passed": test_result["passed"],
        "total": test_result["total"],
        "test_stdout": test_result["stdout"],
        "test_stderr": test_result["stderr"],
    }

    log_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return log_path


def main() -> None:
    if "--serve" in sys.argv:
        start_server()
        return

    teacher_instruction = load_text(TEACH_FILE)
    if not teacher_instruction:
        print("ERROR: teach.md is empty. Write your instructions there first.", file=sys.stderr)
        sys.exit(1)

    prompt = build_prompt()
    print(f"Prompt length: {len(prompt)} chars", file=sys.stderr)

    raw_output = run_talkie(prompt)
    code = extract_code(raw_output)

    print("\n--- Extracted code ---", file=sys.stderr)
    print(code, file=sys.stderr)
    print("--- End code ---\n", file=sys.stderr)

    test_result = run_tests(code)

    log_path = save_result(teacher_instruction, raw_output, code, test_result)

    print(f"Score: {test_result['score']}")
    print(f"Results saved to {log_path}")

    if test_result["failed"] or test_result["errors"]:
        print("\n--- Test output ---")
        print(test_result["stdout"])
        if test_result["stderr"]:
            print(test_result["stderr"])


if __name__ == "__main__":
    main()
