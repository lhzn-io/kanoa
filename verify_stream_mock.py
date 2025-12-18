import sys
from unittest.mock import MagicMock

from kanoa.core.interpreter import AnalyticsInterpreter
from kanoa.core.types import InterpretationChunk, UsageInfo


def verify_streaming_logic():
    print("Verifying streaming logic with Mock Backend...")

    # 1. Mock Backend
    mock_backend = MagicMock()
    mock_backend.backend_name = "mock"

    # Define a generator for interpret
    def mock_interpret_generator(*args, **kwargs):
        yield InterpretationChunk(content="Thinking...", type="status", is_final=False)
        yield InterpretationChunk(content="Hello", type="text", is_final=False)
        yield InterpretationChunk(content=" World", type="text", is_final=False)
        yield InterpretationChunk(
            content="",
            type="usage",
            is_final=True,
            usage=UsageInfo(input_tokens=10, output_tokens=5, cost=0.001),
        )

    mock_backend.interpret.side_effect = mock_interpret_generator

    # 2. Initialize Interpreter and inject mock
    # We initialize with a valid backend name but swap it out
    interp = AnalyticsInterpreter(backend="gemini", model="dummy", api_key="dummy")
    interp.backend = mock_backend

    # 3. Call interpret (streaming)
    print("Calling interpret(stream=True)...")
    iterator = interp.interpret(
        context="test", custom_prompt="Just say hello", stream=True
    )

    chunks = list(iterator)
    print(f"Received {len(chunks)} chunks.")

    if len(chunks) == 4 and chunks[1].content == "Hello":
        print("✅ Streaming OK")
    else:
        print("❌ Streaming FAILED")
        sys.exit(1)

    # Reset mock
    mock_backend.interpret.side_effect = mock_interpret_generator

    # 4. Call interpret (blocking)
    print("\nCalling interpret(stream=False)...")
    result = interp.interpret(
        context="test_blocking", custom_prompt="Hello blocking", stream=False
    )

    print(f"Result type: {type(result)}")
    print(f"Result text: {result.text!r}")

    if result.text == "Hello World":
        print("✅ Blocking OK")
    else:
        print(f"❌ Blocking FAILED. Got: {result.text!r}")
        sys.exit(1)

    print(
        "\n✅ Verification Successful: API handles both stream=True and stream=False correctly."
    )


if __name__ == "__main__":
    verify_streaming_logic()
