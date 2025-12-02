"""
Integration tests for Gemini context cache persistence.

These tests verify that context caches persist across interpreter instances
(simulating kernel restarts) and can be recovered from the server.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from kanoa.backends.gemini import GeminiBackend

from .conftest import get_auth_state

# Load API keys
config_dir = Path.home() / ".config" / "kanoa"
if (config_dir / ".env").exists():
    load_dotenv(config_dir / ".env")


def has_credentials() -> bool:
    """Check for Gemini credentials."""
    return bool(
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or (
            Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        ).exists()
    )


pytestmark = [
    pytest.mark.integration,
    pytest.mark.gemini,
    pytest.mark.caching,
    pytest.mark.skipif(not has_credentials(), reason="No Gemini credentials found"),
]


# Large content to trigger caching (>2048 tokens)
# Using repeated text to ensure we hit the limit easily
CACHE_CONTENT = (
    """
# Persistent Cache Test Document

This document is designed to test the persistence of Gemini context caching.
It needs to be sufficiently long to trigger the caching mechanism.

"""
    + ("The quick brown fox jumps over the lazy dog. " * 500)
    + """

## Section 2: Detailed Analysis

"""
    + ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 500)
)


class TestGeminiCachePersistence:
    """Tests for cache persistence across instances."""

    def test_cache_reuse_across_instances(self) -> None:
        """
        Verify that a cache created by one backend instance can be reused
        by a second instance with the same content (simulating restart).
        """
        auth_state = get_auth_state()
        if auth_state.should_skip("gemini"):
            pytest.skip("Gemini auth previously failed")

        print("\n" + "=" * 60)
        print("🔄 TEST: Cache Persistence (Restart Simulation)")
        print("=" * 60)

        # --- Run 1: Create Cache ---
        print("\n[Instance 1] Initializing...")
        try:
            backend1 = GeminiBackend(
                model="gemini-3-pro-preview",
                verbose=1,
                enable_caching=True,
                cache_ttl_seconds=600,  # 10 mins
            )

            # Ensure we start fresh for this specific content
            # (In a real scenario, we'd want to reuse, but for the test we want to see creation)
            # We can't easily force-clear a specific hash without calculating it,
            # so we'll rely on the logs/metadata to confirm behavior.

            print("[Instance 1] Creating cache...")
            result1 = backend1.create_kb_cache(
                kb_context=CACHE_CONTENT, display_name="kanoa-test-persistence"
            )
            cache_name1 = result1.name

            assert cache_name1 is not None, "Instance 1 failed to create cache"
            print(f"[Instance 1] Cache created: {cache_name1}")

        except Exception as e:
            pytest.fail(f"Instance 1 failed: {e}")

        # --- Run 2: Reuse Cache ---
        print("\n[Instance 2] Initializing (Simulating Restart)...")
        try:
            backend2 = GeminiBackend(
                model="gemini-3-pro-preview",
                verbose=1,
                enable_caching=True,
                cache_ttl_seconds=600,
            )

            print("[Instance 2] Attempting to reuse cache...")
            result2 = backend2.create_kb_cache(
                kb_context=CACHE_CONTENT, display_name="kanoa-test-persistence"
            )
            cache_name2 = result2.name

            assert cache_name2 is not None, "Instance 2 failed to resolve cache"
            print(f"[Instance 2] Cache resolved: {cache_name2}")

            # VERIFICATION
            assert (
                cache_name1 == cache_name2
            ), f"Cache names differ! {cache_name1} vs {cache_name2}"

            print("\n✅ SUCCESS: Cache reused across instances!")

        except Exception as e:
            pytest.fail(f"Instance 2 failed: {e}")
        finally:
            # Cleanup
            if "backend1" in locals() and backend1:
                print("\n[Cleanup] Deleting cache...")
                backend1.clear_cache()
