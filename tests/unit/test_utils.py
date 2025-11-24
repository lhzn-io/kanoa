from kanoa.utils.cost_tracking import CostTracker


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
