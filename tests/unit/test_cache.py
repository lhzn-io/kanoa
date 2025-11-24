from kanoa.knowledge_base.cache import ContextCache


def test_context_cache() -> None:
    cache = ContextCache()

    assert cache.get("key") is None

    cache.set("key", "value")
    assert cache.get("key") == "value"

    cache.clear()
    assert cache.get("key") is None
