"""Run Talkie on the roman-numerals problem and score its solution."""

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


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_prompt() -> str:
    teacher_instruction = load_text(TEACH_FILE)
    introduction = load_text(PROBLEM_DIR / "introduction.md")
    instructions = load_text(PROBLEM_DIR / "instructions.md")

    prompt = (
        f"{teacher_instruction}\n\n"
        f"--- Problem Introduction ---\n{introduction}\n\n"
        f"--- Problem Instructions ---\n{instructions}\n\n"
    )
    return prompt


def extract_code(raw_output: str) -> str:
    """Pull Python code out of the model's response.

    Tries fenced code blocks first, then falls back to the full output.
    """
    fenced = re.search(r"```(?:python)?\s*\n(.+?)```", raw_output, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    # If the model just wrote raw code, return the whole thing.
    return raw_output.strip()


def run_talkie(prompt: str) -> str:
    """Run inference on the Talkie IT model and return its raw text output."""
    sys.path.insert(0, str(ROOT / "src"))
    from talkie import Talkie  # noqa: E402

    print("Loading model…", file=sys.stderr)
    model = Talkie(MODEL_NAME)
    print("Generating…", file=sys.stderr)

    result = model.generate(prompt, temperature=0.7, max_tokens=1024)
    return result.text


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
