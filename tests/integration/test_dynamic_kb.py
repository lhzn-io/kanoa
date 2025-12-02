import pytest

from kanoa.backends.base import InterpretationResult
from kanoa.core.interpreter import AnalyticsInterpreter
from kanoa.core.types import UsageInfo


# Mock backend to avoid actual API calls and costs
class MockBackend:
    def __init__(self, api_key=None, max_tokens=3000, enable_caching=True, **kwargs):
        self.backend_name = "mock"
        self.call_count = 0
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}
        self.last_kb_context = None

    def interpret(
        self,
        fig=None,
        data=None,
        context=None,
        focus=None,
        kb_context=None,
        custom_prompt=None,
        **kwargs,
    ):
        self.call_count += 1
        self.last_kb_context = kb_context

        # Simulate usage
        usage = UsageInfo(input_tokens=100, output_tokens=50, cost=0.01)

        # Update stats (mimicking BaseBackend logic)
        self.total_tokens["input"] += usage.input_tokens
        self.total_tokens["output"] += usage.output_tokens
        self.total_cost += usage.cost

        return InterpretationResult(
            text="Mock interpretation", backend="mock", usage=usage, metadata={}
        )

    def get_cost_summary(self):
        return {
            "backend": self.backend_name,
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "avg_cost_per_call": self.total_cost / max(self.call_count, 1),
        }


@pytest.fixture
def mock_interpreter(monkeypatch):
    # Monkeypatch the backend class resolution
    def mock_get_backend_class(name):
        return MockBackend

    monkeypatch.setattr(
        "kanoa.core.interpreter._get_backend_class", mock_get_backend_class
    )

    return AnalyticsInterpreter(
        backend="mock", api_key="dummy"
    )  # pragma: allowlist secret


def test_with_kb_creates_new_instance(mock_interpreter):
    """Test that with_kb returns a new instance."""
    interp1 = mock_interpreter
    interp2 = interp1.with_kb(kb_content="KB Content")

    assert interp1 is not interp2
    assert interp1.kb is None
    assert interp2.kb is not None
    assert interp2.kb.get_context() == "KB Content"


def test_with_kb_shares_backend_state(mock_interpreter):
    """Test that cost tracking is shared across instances."""
    interp1 = mock_interpreter

    # 1. Call on base interpreter
    interp1.interpret(data={"a": 1})
    summary1 = interp1.get_cost_summary()
    assert summary1["total_calls"] == 1
    assert summary1["total_cost_usd"] == 0.01

    # 2. Create new interpreter with KB
    interp2 = interp1.with_kb(kb_content="KB Content")

    # 3. Call on new interpreter
    interp2.interpret(data={"b": 2})

    # 4. Verify shared state
    summary2 = interp2.get_cost_summary()
    summary1_updated = interp1.get_cost_summary()

    assert summary2["total_calls"] == 2
    assert summary2["total_cost_usd"] == 0.02
    assert summary1_updated["total_calls"] == 2
    assert summary1_updated["total_cost_usd"] == 0.02

    # Verify backend instance identity
    assert interp1.backend is interp2.backend


def test_with_kb_replacement(mock_interpreter):
    """Test that with_kb replaces the existing KB."""
    interp1 = mock_interpreter.with_kb(kb_content="KB 1")
    interp2 = interp1.with_kb(kb_content="KB 2")

    assert interp2.kb.get_context() == "KB 2"
    assert interp1.kb.get_context() == "KB 1"  # Original untouched


def test_kb_context_passing(mock_interpreter):
    """Test that the correct KB context is passed to the backend."""
    interp = mock_interpreter.with_kb(kb_content="Specific Knowledge")
    interp.interpret(data="test")

    assert interp.backend.last_kb_context == "Specific Knowledge"
    interp.interpret(data="test")

    assert interp.backend.last_kb_context == "Specific Knowledge"
