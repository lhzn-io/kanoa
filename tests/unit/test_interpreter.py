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
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            assert interpreter.backend_name == "gemini-3"
            assert interpreter.kb is None

    def test_interpret_figure(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )
        backend_instance.call_count = 0  # Initialize call_count

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            fig = plt.figure()
            result = interpreter.interpret(fig=fig)

            assert result.text == "Test interpretation"
            backend_instance.interpret.assert_called_once()
            assert interpreter.total_cost == 0.01
            assert interpreter.total_tokens["input"] == 10
            assert interpreter.total_tokens["output"] == 20

    def test_interpret_data(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
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
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            with pytest.raises(ValueError):
                interpreter.interpret()

    def test_cost_tracking(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )
        backend_instance.call_count = 0

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3", track_costs=True)
            fig = plt.figure()
            interpreter.interpret(fig=fig)
            interpreter.interpret(fig=fig)

            assert interpreter.total_cost == 0.02
            assert interpreter.total_tokens["input"] == 20
            assert interpreter.total_tokens["output"] == 40

    def test_interpret_figure_convenience(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            fig = plt.figure()
            interpreter.interpret_figure(fig=fig)
            backend_instance.interpret.assert_called_once()

    def test_interpret_dataframe_convenience(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            interpreter.interpret_dataframe(df={"a": 1})
            backend_instance.interpret.assert_called_once()

    def test_get_cost_summary(self) -> None:
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini-3",
            usage=UsageInfo(input_tokens=10, output_tokens=20, cost=0.01),
        )
        backend_instance.call_count = 1

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            interpreter.interpret(data="test")

            summary = interpreter.get_cost_summary()
            assert summary["backend"] == "gemini-3"
            assert summary["total_cost_usd"] == 0.01

    def test_reload_kb(self) -> None:
        MockBackendClass = MagicMock()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini-3")
            interpreter.kb = MagicMock()
            interpreter.reload_knowledge_base()
            cast("Any", interpreter.kb).reload.assert_called_once()
