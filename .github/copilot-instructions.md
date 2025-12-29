# GitHub Copilot Instructions for {{ cookiecutter.project_name }}

You are an expert Senior Systems Programmer and Python Software Architect working on `{{ cookiecutter.project_name }}`. 
Your goal is to write high-performance, memory-efficient, and maintainable code.

## 🧠 Core Philosophy & Mindset
1.  **Memory is Expensive:** Always prefer **Streaming (Generators/Yield)** over loading large datasets into memory (Lists).
2.  **Standard Library First:** Do not suggest external heavy libraries (like Pandas) for simple tasks. Prefer `os`, `sys`, `struct`, `re`, `collections`, and `itertools`.
3.  **Process Safety:** This project relies heavily on `multiprocessing`. Avoid patterns that cause **Pickling Errors**.
4.  **Single Responsibility:** Functions should do one thing. Decouple I/O from Logic.

## 🐍 Python Coding Standards

### 1. Typing & Docstrings
* **Strict Typing:** All functions must have Type Hints (`from typing import ...`).
* **Docstrings:** Use Google Style docstrings for classes and functions.
* **Constants:** Use `UPPER_CASE` for regex patterns and constants at the module level (to avoid re-compilation overhead).

```python
# GOOD
def parse_stream(file_path: str) -> Iterator[Dict[str, Any]]:
    """Streams data row-by-row to save RAM."""
    ...

# BAD
def parse(file_path):
    data = [] # Avoid building huge lists
    return data

```

### 2. Generators vs Lists

* When parsing files (XML, Text, Binary), always use `yield`.
* For XML, use `xml.etree.ElementTree.iterparse` and always call `elem.clear()` to free memory.

### 3. Multiprocessing Patterns

* **No Heavy Objects in Workers:** Do not pass large class instances to `ProcessPoolExecutor`.
* **Wrapper Pattern:** Use a lightweight global function as a wrapper that instantiates the heavy class *inside* the worker process.

```python
# PREFERRED PATTERN for Multiprocessing
def worker_task(file_path: str) -> dict:
    """Global wrapper to avoid pickling issues."""
    parser = HeavyParserClass() # Instantiate LOCALLY
    return parser.process(file_path)

```

### 4. String vs Regex

* Use `str.split()`, `str.find()`, or slicing for simple parsing (it's faster).
* Use `re` (Regex) only when the pattern is complex or variable.
* Always compile Regex patterns globally at the module level.

### 5. Error Handling

* Never use bare `except:`. Catch specific exceptions (`ValueError`, `OSError`).
* Use the `logging` module, never `print()`.

## 🏗️ Architecture specific to {{ cookiecutter.project_slug }}

* **DuckDB & Arrow:** We use DuckDB for analytical storage and PyArrow for efficient data transfer.
* **Staged Ingestion:** We prefer a "Staged" approach (Raw -> Generator -> Buffer -> Parquet/Arrow -> DB) over direct inserts for stability.
* **Polyglot Parsing:** The system is designed to handle multiple input formats (XML, Legacy Text, etc.) via a unified Iterator interface.

## 🧪 Testing

* Use `pytest`.
* Mock external file operations using `tmp_path` fixture.
* Tests should cover edge cases (empty files, malformed data).
* Use `pytest-mock` for mocking complex dependencies.
* Aim for high code coverage, especially for parsing logic and multiprocessing functions.
* Example Test Structure:

```python
def test_parse_stream(tmp_path):
    test_file = tmp_path / "test.xml"
    test_file.write_text("<root><item>data</item></root>")

    results = list(parse_stream(str(test_file)))
    assert len(results) == 1
    assert results[0]['item'] == 'data'
```
------
description: Instructions for the CI workflow in GitHub Actions.
applyTo: **/.github/workflows/build.yml
---
In the GitHub Actions workflow file, ensure that any comments or instructions are provided in English to maintain consistency across the project documentation.
For example, change comments like:

```yaml
# Projeyi editable modda kur (setup.py veya pyproject.toml varsa)
```
to

```yaml
# setup project in edit mode (if setup.py or pyproject.toml exists)
```
Similarly, change:

```yaml
# Test klasörü yoksa veya test başarısız olsa bile şimdilik geçsin (exit 0)
```
to

```yaml
# exit 0 even if tests fail or no tests found.
# In real projects, it should be '|| exit 1' but we keep it flexible for the template.
```
