from kanoa.utils.cost_tracking import CostTracker
from kanoa.utils.notebook import _normalize_latex_for_jupyter


def test_cost_tracker() -> None:
    tracker = CostTracker()
    assert tracker.total_cost == 0.0
    assert tracker.total_tokens["input"] == 0

    tracker.update(input_tokens=100, output_tokens=50, cost=0.05)

    assert tracker.total_cost == 0.05
    assert tracker.total_tokens["input"] == 100
    assert tracker.total_tokens["output"] == 50

    summary = tracker.get_summary()
    assert summary["total_cost_usd"] == 0.05
    assert summary["total_tokens"]["input"] == 100


def test_normalize_latex_for_jupyter() -> None:
    """Test that LaTeX normalization converts broken math to Unicode."""
    # Test broken inline math: $\mu$g/L -> μg/L
    text = r"concentrations of $\mu$g/L and $\sigma$ values"
    result = _normalize_latex_for_jupyter(text)
    assert "μg/L" in result
    assert "σ" in result
    assert r"$\mu$" not in result

    # Test standalone Greek letters
    text2 = r"The value of $\pi$ is approximately 3.14"
    result2 = _normalize_latex_for_jupyter(text2)
    assert "π" in result2

    # Test that proper LaTeX equations are preserved
    # (equations with multiple terms should not be affected)
    text3 = r"The formula is $y = v_0t - \frac{1}{2}gt^2$"
    result3 = _normalize_latex_for_jupyter(text3)
    # This should be unchanged since it's a full equation
    assert r"\frac" in result3
