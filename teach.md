# How to Write a Roman Numeral Converter

You are being asked to produce a piece of text that will be interpreted by a computing machine. The machine understands a precise notation called "Python." Think of it like writing a telegram — every character matters, and the machine follows your instructions to the letter.

## What the machine needs from you

You must produce **exactly one block of code** — nothing else. No commentary, no explanation, no prose. Just the code, enclosed in triple backticks like this:

```python
(your code here)
```

## The notation rules (Python)

1. **`def`** introduces a named procedure — like naming a recipe in a cookbook.
2. **Indentation matters.** Every line inside a procedure must begin with exactly four spaces.
3. **`return`** sends back a result — like writing your answer on a slip of paper and handing it to the examiner.
4. **A list** is written in square brackets: `[1, 2, 3]`
5. **A list of pairs** (called "tuples") looks like: `[(1000, "M"), (900, "CM")]`
6. **A `for` loop** repeats an action for each item in a list. The line ends with a colon, and the body is indented.
7. **`while`** repeats as long as a condition holds true.
8. **`>=`** means "is greater than or equal to."
9. **`+=`** means "append to" (for text) or "add to" (for numbers).
10. **`-=`** means "subtract from."
11. **`""`** is an empty piece of text (a "string").

## The procedure you must write

The procedure is called `roman`. It receives one number and must return the Roman numeral text for that number.

Here is the complete procedure. Copy it exactly:

```python
def roman(number):
    result = ""
    values = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    for value, letters in values:
        while number >= value:
            result += letters
            number -= value
    return result
```

## How it works — an analogy

Imagine you are a bank teller making change. A customer brings you 1996 pennies and asks you to exchange them for the largest denominations first.

- You hand out one 1000-piece (M). Remaining: 996.
- No 1000-pieces left to give. Move to 900-pieces (CM). Hand out one. Remaining: 96.
- Skip 500 and 400 — too large. Move to 90-pieces (XC). Hand out one. Remaining: 6.
- Skip 50 and 40. Move to 10 — too large. Skip. Move to 9 — too large. Move to 5-pieces (V). Hand out one. Remaining: 1.
- Skip 4. Move to 1-pieces (I). Hand out one. Remaining: 0.

Result: M + CM + XC + V + I = MCMXCVI.

## CRITICAL INSTRUCTIONS

- Output ONLY the code block above. Do not write anything before or after it.
- Do not explain the code. Do not add commentary.
- The procedure MUST be named `roman`.
- The procedure MUST accept one argument called `number`.
- The procedure MUST return a string of Roman numeral letters.
- Copy the code EXACTLY as shown — do not alter any part of it.
