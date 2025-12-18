from unittest.mock import MagicMock

from kanoa.utils.notebook import StreamingResultIterator


def test_streaming_result_iterator_auto_executes() -> None:
    # Create a mock generator that behaves like an iterator
    mock_gen = MagicMock()
    mock_gen.__iter__.return_value = mock_gen
    mock_gen.__next__.side_effect = [1, 2, 3, StopIteration]

    # Wrap it
    wrapper = StreamingResultIterator(mock_gen)

    # Simulate IPython display
    wrapper._ipython_display_()

    # Verify it was consumed
    # The loop in _ipython_display_ should have exhausted the iterator
    assert mock_gen.__next__.call_count == 4  # 3 items + StopIteration

    # Verify we can't consume it again via display
    wrapper._ipython_display_()
    # Should not call next again because _started is True
    assert mock_gen.__next__.call_count == 4


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
