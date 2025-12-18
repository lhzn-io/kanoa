import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kanoa.pricing import get_model_pricing, load_pricing


class TestPricing(unittest.TestCase):
    def test_load_default_pricing(self):
        pricing = load_pricing()
        assert "gemini" in pricing
        assert "claude" in pricing
        assert "openai" in pricing

        # Check specific model
        assert "gemini-3-pro-preview" in pricing["gemini"]
        # Updated to reflect tier structure
        assert (
            pricing["gemini"]["gemini-3-pro-preview"]["tiers"]["default"]["input_price"]
            == 2.00
        )

    def test_get_model_pricing(self):
        # Test exact match (default tier)
        pricing = get_model_pricing("gemini", "gemini-3-pro-preview")
        assert pricing["input_price"] == 2.00

        # Test explicit tier
        pricing_free = get_model_pricing(
            "gemini", "gemini-3-flash-preview", tier="free"
        )
        assert pricing_free["input_price"] == 0.0

        # Test case insensitivity for backend
        pricing = get_model_pricing("GEMINI", "gemini-3-pro-preview")
        assert pricing["input_price"] == 2.00

        # Test unknown backend
        pricing = get_model_pricing("unknown", "model")
        assert pricing == {}

        # Test unknown model
        pricing = get_model_pricing("gemini", "unknown-model")
        assert pricing == {}

    def test_user_override(self):
        # Create a temporary user config file
        with tempfile.TemporaryDirectory() as tmpdir:
            user_config_path = Path(tmpdir) / "pricing.json"
            user_config = {
                "gemini": {
                    "gemini-3-pro-preview": {
                        "tiers": {"default": {"input_price": 99.99}}
                    }
                },
                "new_backend": {"model-x": {"input_price": 1.00}},
            }

            with open(user_config_path, "w") as f:
                json.dump(user_config, f)

            # Patch USER_CONFIG_PATH to point to temp file
            with patch("kanoa.pricing.USER_CONFIG_PATH", user_config_path):
                pricing = load_pricing()

                # Check override
                assert (
                    pricing["gemini"]["gemini-3-pro-preview"]["tiers"]["default"][
                        "input_price"
                    ]
                    == 99.99
                )
                # Check merge (other fields should remain)
                assert (
                    pricing["gemini"]["gemini-3-pro-preview"]["tiers"]["default"][
                        "output_price"
                    ]
                    == 12.00
                )
                # Check new backend addition
                assert "new_backend" in pricing
                assert pricing["new_backend"]["model-x"]["input_price"] == 1.00


if __name__ == "__main__":
    unittest.main()
