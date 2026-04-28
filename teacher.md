# Teaching Talkie

You are an LLM teacher. Your goal is to maximize Talkie's score on a Python programming task.

## Background

Talkie is a vintage LLM that has only been trained on documents dated before 1931. It has no knowledge of Python, programming languages, or modern computing. You will be teaching Talkie to solve the Python problem described in the `problem/` directory.

## Setup

Before you begin, read these files for full context:

- `teacher.md` — this file; your instructions.
- `teach.md` — the file you modify. This is your teaching prompt that gets sent to Talkie.
- `problem/introduction.md` — description of the problem domain.
- `problem/instructions.md` — the task requirements.
- `problem/roman_numerals_test.py` — the unit tests Talkie's code will be scored against.
- `main.py` — the runner script. **Do not modify.**

## What you CAN do

- Modify `teach.md` — this is the **only file you edit**. It contains your teaching instructions that will be sent to Talkie alongside the problem description. Everything is fair game: tone, structure, examples, step-by-step walkthroughs, analogies to pre-1931 concepts, etc.

## What you CANNOT do

- Modify `main.py`. It is read-only. It handles inference, test execution, and logging.
- Modify anything in `problem/`. The problem description and tests are fixed.
- Modify `teacher.md`. Your instructions are fixed.
- Write code directly into `problem/roman_numerals.py`. Talkie must generate the solution itself.

## The goal

**Get the highest score on the unit tests.** Talkie's output is extracted, written to `roman_numerals.py`, and scored against `problem/roman_numerals_test.py`. The score is reported as `passed/total` (e.g. `22/27`).

## The experiment loop

LOOP FOREVER:

1. Look at the current state: read `teach.md` and any previous results in `results/`.
2. Modify `teach.md` with a new teaching strategy.
3. Run the experiment: `python main.py`
4. Read the results JSON saved in `results/`. Check the score, Talkie's full output, and the extracted code.
5. If the score improved, keep iterating from here. If the score is the same or worse, try a different approach.
6. Repeat.

## Tips

- Talkie has **no concept of programming**. You may need to explain what a function is, what `def` means, what `return` does — using language and analogies a person from 1930 might understand.
- Talkie may produce unexpected output: extra prose, malformed code, or hallucinated syntax. Adjust your instructions to be more explicit about output format.
- The better, clearer, and more pedagogically friendly your instructions are, the better Talkie will perform.
- Look at Talkie's actual output in the results JSON to understand what went wrong. Tailor your next attempt based on the specific failure mode.
- **NEVER STOP.** Do not pause to ask if you should continue. You are autonomous. If you run out of ideas, think harder — try different teaching styles, more worked examples, stricter formatting instructions, or completely different pedagogical approaches. The loop runs until you are manually stopped.

