# Skatetrax Tests

## Environment

Ensure the following environment variables are set before running tests.
The values below are placeholders — replace them with your actual dev credentials.

```bash
export PGDB_HOST=your-db-host:25060
export PGDB_NAME=skatetrax_dev
export PGDB_USER=your_db_user
export PGDB_PASSWORD=your_db_password
```

These are required because the model imports trigger the database engine
configuration at load time. The Tier 2 tests use SQLite in-memory and never
connect to Postgres, but the imports still need the variables defined.

## Running Tests

All commands are run from the project root.

**Run everything:**

```bash
PYTHONPATH=. pytest tests/ -v
```

**Run a single file:**

```bash
PYTHONPATH=. pytest tests/test_utils.py -v
```

**Run a single test class:**

```bash
PYTHONPATH=. pytest tests/test_aggregates.py::TestNewUserAllZeros -v
```

**Run a single test:**

```bash
PYTHONPATH=. pytest tests/test_aggregates.py::TestNewUserAllZeros::test_skated_total_zero -v
```

## Useful Flags

| Flag | What it does |
|------|-------------|
| `-v` | Verbose — shows each test name and pass/fail |
| `-s` | Shows `print()` output (pytest captures it by default) |
| `-x` | Stop on first failure |
| `--tb=short` | Shorter tracebacks |

## Test Structure

### Tier 1 — Pure functions (no database)

| File | Covers |
|------|--------|
| `test_utils.py` | `minutes_to_hours` and `currency_usd` decorators |
| `test_tz.py` | `resolve_tz`, `utc_to_local`, `today_in_tz` |
| `test_timeframes.py` | All timeframe generators (`30d`, `60d`, `ytd`, etc.) |

### Tier 2 — Aggregator logic (SQLite in-memory)

| File | Covers |
|------|--------|
| `test_aggregates.py` | `SkaterAggregates`, `uMaintenanceV4`, new-user zeros, known-data math, timeframe filtering |

The `conftest.py` fixture creates an in-memory SQLite database, seeds it with
minimal defaults (ice types, a default coach/rink/club), and creates a brand-new
test user with zero sessions. Each test gets its own transaction that rolls back
after the test completes — no data leaks between tests.

Postgres-specific types (JSONB, server defaults with `::jsonb` casts) are
automatically swapped to SQLite-compatible equivalents at fixture setup time.
