from typing import Any, cast
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from kanoa.core.interpreter import AnalyticsInterpreter
from kanoa.core.types import InterpretationResult, UsageInfo


class TestAnalyticsInterpreter:
    def test_initialization(self) -> None:
        MockBackendClass = MagicMock()
        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            assert interpreter.backend_name == "gemini"
            assert interpreter.kb is None

    def test_interpret_figure(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value

        # Configure side effect to simulate cost updates
        def interpret_side_effect(*args, **kwargs):
            backend_instance.total_cost += 0.01
            backend_instance.total_tokens["input"] += 10
            backend_instance.total_tokens["output"] += 20
            return InterpretationResult(
                text="Test interpretation",
                backend="gemini",
                usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
            )

        backend_instance.interpret.side_effect = interpret_side_effect
        backend_instance.total_cost = 0.0
        backend_instance.total_tokens = {"input": 0, "output": 0}
        backend_instance.call_count = 0  # Initialize call_count

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            fig = plt.figure()
            result = interpreter.interpret(fig=fig)

            assert result.text == "Test interpretation"
            backend_instance.interpret.assert_called_once()
            assert interpreter.backend.total_cost == 0.01
            assert interpreter.backend.total_tokens["input"] == 10
            assert interpreter.backend.total_tokens["output"] == 20

    def test_interpret_data(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            data = {"key": "value"}
            result = interpreter.interpret(data=data)

            assert result.text == "Test interpretation"
            backend_instance.interpret.assert_called_once()

    def test_interpret_no_input(self) -> None:
        MockBackendClass = MagicMock()
        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            with pytest.raises(ValueError):
                interpreter.interpret()

    def test_cost_tracking(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value

        # Configure side effect to simulate cost updates
        def interpret_side_effect(*args, **kwargs):
            backend_instance.total_cost += 0.01
            backend_instance.total_tokens["input"] += 10
            backend_instance.total_tokens["output"] += 20
            return InterpretationResult(
                text="Test interpretation",
                backend="gemini",
                usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
            )

        backend_instance.interpret.side_effect = interpret_side_effect
        backend_instance.total_cost = 0.0
        backend_instance.total_tokens = {"input": 0, "output": 0}
        backend_instance.call_count = 0

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini", track_costs=True)
            fig = plt.figure()
            interpreter.interpret(fig=fig)
            interpreter.interpret(fig=fig)

            assert interpreter.backend.total_cost == 0.02
            assert interpreter.backend.total_tokens["input"] == 20
            assert interpreter.backend.total_tokens["output"] == 40

    def test_interpret_figure_convenience(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            fig = plt.figure()
            interpreter.interpret_figure(fig=fig)
            backend_instance.interpret.assert_called_once()

    def test_interpret_dataframe_convenience(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            interpreter.interpret_dataframe(df={"a": 1})
            backend_instance.interpret.assert_called_once()

    def test_get_cost_summary(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )
        backend_instance.get_cost_summary.return_value = {
            "backend": "gemini",
            "total_cost_usd": 0.01,
        }
        backend_instance.call_count = 1

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            interpreter.interpret(data="test")

            summary = interpreter.get_cost_summary()
            assert summary["backend"] == "gemini"
            assert summary["total_cost_usd"] == 0.01

    def test_reload_kb(self) -> None:
        MockBackendClass = MagicMock()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            interpreter.kb = MagicMock()
            interpreter.reload_knowledge_base()
            cast("Any", interpreter.kb).reload.assert_called_once()
