# Stack rules: Python

(A starting reference: keep what fits your project.)

## Detection markers
`requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `*.py`, `Pipfile`, virtualenv dirs.

## Commands (verify they exist before claiming you ran them)
- **Run:** `python3 <script.py>` (check how the project runs its scripts, e.g. from the repo root).
- **Test:** `pytest` if present, else `python3 -m unittest`. If neither is configured, say so — do not pretend tests exist.
- **Lint/format/type:** `ruff` / `flake8`, `black`, `mypy` — only if configured in the repo (check pyproject.toml / setup.cfg / pre-commit). Don't introduce a tool the project doesn't use.
- **Deps:** `pip install` (prefer the project's virtualenv over the system Python); honor `requirements.txt` / `pyproject.toml`.

## Conventions
- PEP 8; type hints on public functions; prefer `pathlib` over string paths; f-strings.
- No mutable default arguments. Prefer pure functions; isolate side effects/IO.
- Follow the surrounding module's existing style first.

## Instrumentation style (for plan/implement skills)
- Use the `logging` module gated by a `--debug` flag or env var, or a `if DEBUG:` guard — NOT bare `print()` spam.
- Event-based, not per-iteration in hot loops.
- Mark debug code so it's trivially removable; remove or gate before commit.

## Risk checklist (surface any that this change touches)
- **Float precision** — large integers/IDs beyond float64 mantissa; money math; `==` on floats.
- **pandas** — `dtype` correctness on read (esp. ID columns with NaN that silently become float64), `SettingWithCopyWarning`, chained indexing, index alignment.
- **Time-series / modelling** — using data from the future (look-ahead), target leakage; train/score time alignment.
- **Reproducibility** — unseeded randomness; non-deterministic ordering; idempotency (same input -> same output / byte-identical artifacts).
- **Scale/memory** — large CSV/DataFrame loads; copies; chunking.
- **Concurrency** — multiprocessing pickling, file locking on shared writes, the GIL.
- **IO** — atomic writes (write-temp-then-replace), file-exists/permission handling, encoding.
- **Secrets** — never log API keys / `.env` values.

## Verification style
- Run the actual script or `pytest`; paste real output, not expected output.
- For data work, sanity-check row counts, dtypes, null counts, and a few sample rows.
- Prefer a tiny reproducible slice over "looks right".
