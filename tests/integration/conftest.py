"""
Integration test configuration and safety mechanisms.

This is a pytest `conftest.py` file, which is the standard way to share fixtures
and configuration across test files in pytest. This particular conftest provides:

**Cost Protection Features:**
1. **Rate Limiting**: Prevents excessive API usage by enforcing:
   - Minimum 5-minute interval between test runs
   - Maximum 20 runs per 24-hour period
   - Configurable via MIN_RUN_INTERVAL and MAX_RUNS_PER_DAY constants

2. **Smart Counting**: Only counts successful test executions (passed/failed),
   not skipped tests due to missing credentials. This prevents the rate limit
   from being triggered when tests can't actually run.

3. **Override Mechanisms**:
   - CLI flag: `pytest --force-integration`
   - Environment variable: `KANOA_SKIP_RATE_LIMIT=1`
   - Manual: Remove lock file at `~/.config/kanoa/.integration_test_lock`

**Authentication Features:**
- **Lazy Auth Checking**: Instead of checking file existence upfront, we attempt
  to initialize the backend and skip remaining tests if auth fails.
- **Shared State**: Auth failures are tracked per-backend so a failure in one
  test skips subsequent tests for that backend.

**User Experience Features:**
- **Helpful Skip Reasons**: Tests skip with concise messages that link to
  the authentication documentation for setup instructions.

**File Location:**
The lock file is stored in `~/.config/kanoa/.integration_test_lock` and tracks:
- Last run timestamp
- List of recent run timestamps (for daily limit calculation)

**Usage:**
- Normal run: `pytest tests/integration/`
- Force run: `pytest tests/integration/ --force-integration`
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

# Cost protection: Minimum time between integration test runs (in seconds)
MIN_RUN_INTERVAL = 300  # 5 minutes
MAX_RUNS_PER_DAY = 20

# Lock file to track test runs
LOCK_FILE = Path.home() / ".config" / "kanoa" / ".integration_test_lock"


# Shared state for tracking auth failures across tests
class AuthState:
    """Track authentication state for backends to enable lazy auth checking."""

    def __init__(self) -> None:
        # Maps backend name -> error message (None = not checked, "" = OK)
        self._failures: Dict[str, Optional[str]] = {}

    def mark_auth_failed(self, backend: str, error: str) -> None:
        """Record an auth failure for a backend."""
        self._failures[backend] = error

    def mark_auth_ok(self, backend: str) -> None:
        """Record successful auth for a backend."""
        self._failures[backend] = ""

    def should_skip(self, backend: str) -> Optional[str]:
        """
        Check if tests for this backend should be skipped.

        Returns:
            None if auth hasn't been checked yet or succeeded.
            Error message string if auth has failed.
        """
        error = self._failures.get(backend)
        if error:  # Non-empty string means failure
            return error
        return None

    def is_checked(self, backend: str) -> bool:
        """Check if auth has been verified for this backend."""
        return backend in self._failures


# Global auth state instance
_auth_state = AuthState()


def get_auth_state() -> AuthState:
    """Get the global auth state tracker."""
    return _auth_state


# Cost tracking for integration tests
class CostTracker:
    """Track API costs across integration tests for reporting."""

    def __init__(self) -> None:
        self._costs: List[Tuple[str, float]] = []  # (test_name, cost)
        self._total: float = 0.0

    def record(self, test_name: str, cost: float) -> None:
        """Record a cost for a test."""
        self._costs.append((test_name, cost))
        self._total += cost

    def get_total(self) -> float:
        """Get total cost across all tests."""
        return self._total

    def get_all(self) -> List[Tuple[str, float]]:
        """Get all recorded costs."""
        return self._costs.copy()

    def print_summary(self) -> None:
        """Print a summary of all costs."""
        if not self._costs:
            return

        print("\n" + "=" * 60)
        print("💰 INTEGRATION TEST COST SUMMARY")
        print("=" * 60)
        for test_name, cost in self._costs:
            # Shorten test name for display
            short_name = test_name.split("::")[-1] if "::" in test_name else test_name
            print(f"  {short_name}: ${cost:.6f}")
        print("-" * 60)
        print(f"  TOTAL: ${self._total:.6f}")
        print("=" * 60)


# Global cost tracker instance
_cost_tracker = CostTracker()


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker."""
    return _cost_tracker


def check_rate_limit() -> None:
    """
    Check if integration tests can run based on rate limiting.

    Raises:
        pytest.skip: If tests are being run too frequently
    """
    if not LOCK_FILE.exists():
        return

    try:
        with open(LOCK_FILE, "r") as f:
            data = json.load(f)
            last_run = data.get("last_run", 0)
            runs_today = data.get("runs_today", [])

            now = time.time()

            # Check minimum interval
            time_since_last = now - last_run
            if time_since_last < MIN_RUN_INTERVAL:
                wait_time = int(MIN_RUN_INTERVAL - time_since_last)
                pytest.skip(
                    f"Integration test rate limit: last run {int(time_since_last)}s "
                    f"ago, wait {wait_time}s more (rm {LOCK_FILE} to override)"
                )

            # Check daily limit
            one_day_ago = now - 86400
            runs_today = [r for r in runs_today if r > one_day_ago]
            if len(runs_today) >= MAX_RUNS_PER_DAY:
                pytest.skip(
                    f"Daily integration test limit reached: "
                    f"{len(runs_today)}/{MAX_RUNS_PER_DAY} runs "
                    f"(rm {LOCK_FILE} to override)"
                )
    except (json.JSONDecodeError, KeyError):
        pass  # Ignore corrupted lock file


def update_rate_limit() -> None:
    """Update the lock file with the current run."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()

    runs_today = []
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, "r") as f:
                data = json.load(f)
                runs_today = data.get("runs_today", [])
        except (json.JSONDecodeError, KeyError):
            pass

    # Filter old runs and add new one
    one_day_ago = now - 86400
    runs_today = [r for r in runs_today if r > one_day_ago]
    runs_today.append(now)

    with open(LOCK_FILE, "w") as f:
        json.dump(
            {
                "last_run": now,
                "runs_today": runs_today[-MAX_RUNS_PER_DAY:],
            },
            f,
        )


def pytest_addoption(parser):
    """Add custom pytest command line options."""
    parser.addoption(
        "--force-integration",
        action="store_true",
        default=False,
        help="Force run integration tests, bypassing rate limits",
    )


@pytest.fixture(scope="session", autouse=True)
def integration_test_safety(request):
    """Session-level fixture to enforce rate limiting on integration tests."""
    # Only apply rate limiting if running integration tests
    # Check if any integration markers are present in the session
    session = request.session
    has_integration_tests = any(
        item.get_closest_marker(mark) is not None
        for item in session.items
        for mark in ["integration", "gemini", "claude", "molmo", "openai"]
    )

    if has_integration_tests:
        # Allow override via CLI flag or environment variable
        force_run = request.config.getoption("--force-integration")
        if not force_run and os.environ.get("KANOA_SKIP_RATE_LIMIT") != "1":
            check_rate_limit()

    yield

    # Only update rate limit if tests actually ran (passed or failed)
    # We check terminalreporter stats to see if any tests were executed
    if has_integration_tests:
        tr = request.config.pluginmanager.get_plugin("terminalreporter")
        if tr:
            passed = len(tr.stats.get("passed", []))
            failed = len(tr.stats.get("failed", []))

            # Update only if we had actual executions
            if passed + failed > 0:
                update_rate_limit()

        # Print cost summary at the end of the session
        _cost_tracker.print_summary()
