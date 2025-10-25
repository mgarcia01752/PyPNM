# PyPNM Test Guide (pytest)

This page is the **main index for testing** PyPNM with `pytest`. It covers setup, running unit/integration tests, markers, logging, coverage, and common troubleshooting.

---

## Quick Start

```bash
# From repo root, in your virtualenv
pip install -e ".[dev]"         # installs pytest, pytest-cov, etc.
pytest -q                        # run the whole suite
```

Common invocations:

```bash
pytest -vv                                  # verbose
pytest -k rxmer                              # substring match on test names/paths
pytest -m pnm                                # only PNM parser tests
pytest -m "pnm and not slow"                 # combine markers
pytest tests/test_pnm_rxmer_parse.py::test_rxmer_file_loads_and_models_ok
```

---

## Project Test Layout

- **`tests/`** – all tests live here.
- **`tests/_data/`** – sample PNM binaries used by parser tests:
  - `rxmer.bin`, `fec_summary.bin`, `const_display.bin`,
    `histogram.bin`, `modulation_profile.bin`, `channel_estimation.bin`,
    `spectrum_analyzer.bin`
- Integration tests for real gear (SNMP, ping) are also under `tests/` and use markers to opt-in.

Python path during tests is configured to include `src/` (see *pyproject.toml*).

---

## Markers

Markers are configured in **`pyproject.toml`** → `[tool.pytest.ini_options]`.

Currently available:

- `pnm` – PNM file parsing/processing tests (use sample binaries in `tests/_data/`)
- `net` – tests that require real network access (e.g., SNMP to a CM)
- `slow` – long‑running tests

Examples:

```bash
pytest -m pnm
pytest -m "net and not slow"
```

> **Tip:** If you see `Failed: 'XYZ' not found in markers`, add the marker to `pyproject.toml` under `markers = [...]`.

---

## Async Tests

We use `pytest-asyncio` (mode=auto). You can write async tests as usual:
```python
import pytest

@pytest.mark.asyncio
async def test_async_thing():
    ...
```
You can also run sync wrappers around async calls using `asyncio.run(...)` as needed.

---

## Logging & Debugging

Enable live logs during test runs:

```bash
pytest -vv -o log_cli=true -o log_cli_level=DEBUG
```

Per‑module logging can be controlled in code via standard `logging.getLogger(__name__)` usage.

We also silence some upstream deprecation warnings from `pysmi/pysnmp` via `filterwarnings` in `pyproject.toml`. To see everything, run with:

```bash
pytest -W default
```

---

## Coverage

We ship `pytest-cov` for coverage reporting:

```bash
pytest --cov=pypnm --cov-report=term-missing
pytest --cov=pypnm --cov-report=html  # writes htmlcov/index.html
```

---

## Real-Gear (SNMP) Integration Tests

A few tests talk to actual devices (ping/SNMP). They are **opt-in** by marker:

```bash
# Only run networked tests
pytest -m net -vv

# Or run a single test module
pytest tests/test_cable_modem_snmpv2_integration.py -vv -m net
```

Environment setup (examples):

- **Target CM IP / hostname** – set in the test module or via env var.
- **SNMP** – community string, port, and timeouts should be configured either in env (`.env`) or test fixtures.

If you consistently see timeouts in CI but not locally, consider:
- Increasing SNMP timeouts/retries in the fixture.
- Ensuring the test network path is reachable from your runner.
- Skipping with `-m "not net"` for CI workflows that lack device access.

---

## PNM Parser Tests

PNM parsers are tested against sample files under `tests/_data/`. Typical checks include:
- Header parsing (`PnmHeader`)
- Model shape/fields for each parser
- Numeric ranges & monotonic sequences (e.g., frequencies, amplitudes)
- JSON/Dict round‑trip

Run all PNM parser tests:

```bash
pytest -m pnm -vv
```

Example: focus only on RxMER tests:

```bash
pytest -k rxmer -m pnm -vv
```

---

## Test Selection Cheatsheet

```bash
pytest -k "spectrum and not json"          # include/exclude by name
pytest tests/test_pnm_histogram_parse.py   # by file
pytest path/to/test_file.py::test_case     # single test
```

---

## Useful Options

- `-x` – stop after first failure
- `--maxfail=2` – stop after 2 failures
- `-q` – quiet
- `-vv` – very verbose
- `--lf` – run last failed tests
- `--ff` – run failed first, then rest
- `--durations=10` – show 10 slowest tests

---

## CI Hints

- Skip network‑dependent tests unless runners have access:
  ```bash
  pytest -m "not net"
  ```
- Generate coverage:
  ```bash
  pytest --cov=pypnm --cov-report=xml
  ```
- Cache your `.pytest_cache/` between runs (optional).

---

## Troubleshooting

**Marker not found**
```
Failed: 'pnm' not found in `markers` configuration option
```
→ Add `pnm` to `pyproject.toml` under `[tool.pytest.ini_options].markers`.

**ImportError / ModuleNotFoundError**
- Ensure `src/` is on the path (it is by default via `pyproject.toml`).
- Use `pip install -e .` (editable) to keep imports working during dev.

**Asyncio timeouts**
- Use `pytest -vv -o log_cli=true` to see where it hangs.
- Wrap awaits with `asyncio.wait_for(..., timeout=SECONDS)` in tests when appropriate.

**Deprecation warnings from pysmi/pysnmp**
- We’ve migrated to the newer API where possible.
- In tests, `filterwarnings` suppresses the known deprecations (see `pyproject.toml`).

---

## Reference: Our PyTest Config (excerpt)

From `pyproject.toml`:
```toml
[tool.pytest.ini_options]
minversion = "8.0"
pythonpath = ["src"]
testpaths  = ["tests"]
addopts    = "-ra -q --strict-markers --tb=short"
markers = [
  "slow: slow tests",
  "net: network-required tests",
  "pnm: PNM parser tests",
]
# Optional noise control
filterwarnings = [
  "ignore:.*getReadersFromUrls.*:DeprecationWarning:pysmi.reader.url",
  "ignore:.*addSources.*:DeprecationWarning:pysnmp.smi.compiler",
  "ignore:.*addSearchers.*:DeprecationWarning:pysnmp.smi.compiler",
  "ignore:.*addBorrowers.*:DeprecationWarning:pysnmp.smi.compiler",
]
```

---

## See Also

- [pytest docs](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- `pysnmp` / `pysmi` docs for SNMP integration specifics.
