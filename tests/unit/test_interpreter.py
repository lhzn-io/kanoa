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

    def test_get_prompts(self) -> None:
        """Test get_prompts() method returns prompt templates."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value

        # Mock the prompt_templates attribute
        from kanoa.utils.prompts import PromptTemplates

        backend_instance.prompt_templates = PromptTemplates()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            prompts = interpreter.get_prompts()

            assert "system_prompt" in prompts
            assert "user_prompt" in prompts
            assert "You are an expert data analyst" in prompts["system_prompt"]
            assert "Analyze this analytical output" in prompts["user_prompt"]

    def test_preview_prompt_without_kb(self) -> None:
        """Test preview_prompt() without knowledge base."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance._build_prompt.return_value = "Test prompt"

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            prompt = interpreter.preview_prompt(
                context="Sales data", focus="YoY growth"
            )

            assert prompt == "Test prompt"
            backend_instance._build_prompt.assert_called_once()
            call_args = backend_instance._build_prompt.call_args
            assert call_args[1]["context"] == "Sales data"
            assert call_args[1]["focus"] == "YoY growth"
            assert call_args[1]["kb_context"] is None

    def test_preview_prompt_with_kb(self) -> None:
        """Test preview_prompt() with knowledge base."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance._build_prompt.return_value = "Test prompt with KB"
        backend_instance.encode_kb.return_value = "KB content"

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            interpreter.kb = MagicMock()

            prompt = interpreter.preview_prompt(
                context="Sales data", include_kb=True
            )

            assert prompt == "Test prompt with KB"
            backend_instance.encode_kb.assert_called_once()
            backend_instance._build_prompt.assert_called_once()
            call_args = backend_instance._build_prompt.call_args
            assert call_args[1]["kb_context"] == "KB content"

    def test_preview_prompt_custom(self) -> None:
        """Test preview_prompt() with custom prompt."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        backend_instance._build_prompt.return_value = "Custom prompt"

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")
            prompt = interpreter.preview_prompt(custom_prompt="Custom prompt")

            assert prompt == "Custom prompt"
            backend_instance._build_prompt.assert_called_once()
            call_args = backend_instance._build_prompt.call_args
            assert call_args[1]["custom_prompt"] == "Custom prompt"

    def test_init_with_custom_prompts(self) -> None:
        """Test initialization with custom prompt templates."""
        MockBackendClass = MagicMock()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            custom_system = "You are a financial analyst..."
            custom_user = "Analyze this data..."

            interpreter = AnalyticsInterpreter(
                backend="gemini",
                system_prompt=custom_system,
                user_prompt=custom_user,
            )

            # Check that backend was initialized with custom prompt templates
            init_call = MockBackendClass.call_args
            assert "prompt_templates" in init_call[1]
            templates = init_call[1]["prompt_templates"]
            assert templates is not None
            assert templates.system_prompt == custom_system
            assert templates.user_prompt == custom_user

    def test_set_prompts(self) -> None:
        """Test set_prompts() method."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value

        from kanoa.utils.prompts import PromptTemplates

        # Set initial templates
        backend_instance.prompt_templates = PromptTemplates()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")

            # Test chaining
            result = interpreter.set_prompts(
                system_prompt="New system prompt",
                user_prompt="New user prompt",
            )

            assert result is interpreter  # Check chaining
            assert (
                interpreter.backend.prompt_templates.system_prompt
                == "New system prompt"
            )
            assert interpreter.backend.prompt_templates.user_prompt == "New user prompt"

    def test_set_prompts_partial(self) -> None:
        """Test set_prompts() with partial updates."""
        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value

        from kanoa.utils.prompts import PromptTemplates

        original_templates = PromptTemplates(
            system_prompt="Original system",
            user_prompt="Original user",
        )
        backend_instance.prompt_templates = original_templates

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(backend="gemini")

            # Update only system prompt
            interpreter.set_prompts(system_prompt="New system prompt")

            assert (
                interpreter.backend.prompt_templates.system_prompt
                == "New system prompt"
            )
            assert (
                interpreter.backend.prompt_templates.user_prompt == "Original user"
            )  # Unchanged

    def test_set_prompts_chaining_with_kb(self) -> None:
        """Test set_prompts() chaining with with_kb()."""
        MockBackendClass = MagicMock()

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ), patch("kanoa.core.interpreter.KnowledgeBaseManager"):
            interpreter = AnalyticsInterpreter(backend="gemini")

            # Test chaining set_prompts with with_kb
            result = interpreter.set_prompts(
                system_prompt="Custom prompt"
            ).with_kb(kb_content="Test KB")

            # Result should be a new interpreter instance from with_kb
            assert result is not interpreter
            assert result.kb is not None
