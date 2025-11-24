from kanoa.backends.molmo import MolmoBackend


def test_molmo_stub() -> None:
    backend = MolmoBackend()
    result = backend.interpret(
        fig=None,
        data=None,
        context=None,
        focus=None,
        kb_context=None,
        custom_prompt=None,
    )
    assert "not implemented" in result.text
    assert result.backend == "molmo"
