"""Quick interactive inference shell for Talkie.

Uses the model server (main.py --serve) when available, otherwise loads
the model in-process. Output is streamed token-by-token.

Usage:
    uv run infer.py                  # interactive REPL
    uv run infer.py -f teach.md      # run a single file as prompt and exit
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Generator

ROOT = Path(__file__).resolve().parent

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5193

_local_model = None


def _server_is_running() -> bool:
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


def _stream_via_server(prompt: str, max_tokens: int = 1024) -> Generator[str, None, None]:
    body = json.dumps({
        "prompt": prompt, "temperature": 0.7,
        "max_tokens": max_tokens, "stream": True,
    })
    req = urllib.request.Request(
        f"http://{SERVER_HOST}:{SERVER_PORT}/",
        data=body.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=300)
    for line in resp:
        line = line.decode().strip()
        if not line:
            continue
        data = json.loads(line)
        if "token" in data:
            yield data["token"]
        if data.get("done"):
            break


def _get_local_model():
    global _local_model
    if _local_model is None:
        sys.path.insert(0, str(ROOT / "src"))
        from talkie import Talkie

        print("No server found. Loading model locally (slow)…", file=sys.stderr)
        _local_model = Talkie("talkie-1930-13b-it")
        print("Model ready.\n", file=sys.stderr)
    return _local_model


def _stream_local(prompt: str, max_tokens: int = 1024) -> Generator[str, None, None]:
    model = _get_local_model()
    yield from model.stream(prompt, temperature=0.7, max_tokens=max_tokens)


def stream_prompt(prompt: str, max_tokens: int = 1024) -> Generator[str, None, None]:
    if _server_is_running():
        yield from _stream_via_server(prompt, max_tokens)
    else:
        yield from _stream_local(prompt, max_tokens)


def repl() -> None:
    use_server = _server_is_running()
    if use_server:
        print("=== Talkie REPL (using model server) ===")
    else:
        print("=== Talkie REPL (loading model locally — start `uv run main.py --serve` for faster runs) ===")
        _get_local_model()

    print("Commands:")
    print("  :file <path>   — load a file as the prompt")
    print("  :quit          — exit")
    print("  (anything else) — send as prompt")
    print()

    while True:
        try:
            prompt = input("prompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not prompt:
            continue
        if prompt == ":quit":
            break
        if prompt.startswith(":file "):
            path = Path(prompt[6:].strip())
            if not path.is_absolute():
                path = ROOT / path
            if not path.exists():
                print(f"File not found: {path}", file=sys.stderr)
                continue
            prompt = path.read_text(encoding="utf-8").strip()
            print(f"[loaded {len(prompt)} chars from {path.name}]")

        print()
        for token in stream_prompt(prompt):
            print(token, end="", flush=True)
        print("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick Talkie inference")
    parser.add_argument("-f", "--file", help="Run a single file as prompt and exit")
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = ROOT / path
        prompt = path.read_text(encoding="utf-8").strip()
        print(f"[Prompt: {len(prompt)} chars from {path.name}]", file=sys.stderr)
        for token in stream_prompt(prompt, max_tokens=args.max_tokens):
            print(token, end="", flush=True)
        print()
    else:
        repl()


if __name__ == "__main__":
    main()
