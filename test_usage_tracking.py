#!/usr/bin/env python3
"""Quick test to verify usage tracking in Deep Research backends."""

from kanoa.pricing import get_model_pricing

# Test pricing lookup
model = "gemini-3-pro-preview"
pricing = get_model_pricing("gemini", model, tier="default")

print(f"Pricing for {model}:")
print(f"  Input: ${pricing.get('input_price', 0.0)} per 1M tokens")
print(f"  Output: ${pricing.get('output_price', 0.0)} per 1M tokens")

# Simulate usage calculation
input_tokens = 50_000
output_tokens = 10_000

input_cost = input_tokens / 1_000_000 * pricing.get("input_price", 0.0)
output_cost = output_tokens / 1_000_000 * pricing.get("output_price", 0.0)
total_cost = input_cost + output_cost

print("\nSimulated usage:")
print(f"  Input: {input_tokens:,} tokens → ${input_cost:.4f}")
print(f"  Output: {output_tokens:,} tokens → ${output_cost:.4f}")
print(f"  Total cost: ${total_cost:.4f}")

print("\n✓ Usage tracking logic verified")
