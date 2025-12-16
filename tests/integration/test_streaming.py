import pytest

# Basic mock for testing streaming if backend not available?
# No, we want integration test with real backend if possible.
# But we can also test valid iterator structure.
# We will use Gemini if available, else skip.
from .test_gemini_integration import has_potential_credentials


@pytest.mark.integration
@pytest.mark.streaming
@pytest.mark.skipif(not has_potential_credentials(), reason="No Gemini credentials")
def test_streaming_gemini():
    from kanoa.core.interpreter import AnalyticsInterpreter

    try:
        interp = AnalyticsInterpreter(backend="gemini", model="gemini-2.5-flash")
    except Exception as e:
        pytest.skip(f"Backend init failed: {e}")

    print("\n--- Testing Streaming ---")
    iterator = interp.interpret(
        custom_prompt="Write a short poem about coding.",
        display_result=False,  # Handle manually
    )

    chunks = []
    print("[stream] ", end="", flush=True)

    for chunk in iterator:
        chunks.append(chunk)
        if chunk.type == "text":
            print(chunk.content, end="", flush=True)
        elif chunk.type == "status":
            print(f"\n[status] {chunk.content}")
        elif chunk.type == "usage":
            pass  # Will print at end

    print("\n")  # Newline after stream
    assert len(chunks) > 0

    # Verify text accumulation
    full_text = "".join(c.content for c in chunks if c.type == "text")
    assert len(full_text) > 0

    # Verify usage and print cost
    usage_chunks = [c for c in chunks if c.type == "usage"]
    assert len(usage_chunks) == 1
    usage = usage_chunks[0].usage
    assert usage is not None
    assert usage.input_tokens > 0

    print("-" * 30)
    print(f"[cost] ${usage.cost:.6f}")
    print(f"[usage] Input: {usage.input_tokens}, Output: {usage.output_tokens}")
    print("-" * 30)
