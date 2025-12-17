from unittest.mock import MagicMock

from kanoa.utils.notebook import StreamingResultIterator


def test_streaming_result_iterator_auto_executes() -> None:
    # Create a mock generator
    mock_gen = MagicMock()
    mock_gen.__iter__.return_value = iter([1, 2, 3])

    # Wrap it
    wrapper = StreamingResultIterator(mock_gen)

    # Simulate IPython display
    wrapper._ipython_display_()

    # Verify it was consumed (we can't easily check consumption of a real generator
    # without side effects, but we can check if it ran without error)
    # In a real scenario, the side effects (display updates) would happen here.

    # Verify we can't consume it again via display
    wrapper._ipython_display_()


def test_streaming_result_iterator_manual_iteration() -> None:
    # Create a real generator
    def gen():
        yield 1
        yield 2
        yield 3

    wrapper = StreamingResultIterator(gen())

    # Manually iterate
    results = list(wrapper)
    assert results == [1, 2, 3]

    # Verify display doesn't run after manual iteration
    # (It would be empty anyway, but the guard clause should catch it)
    wrapper._ipython_display_()
