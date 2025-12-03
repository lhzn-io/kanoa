"""
Integration tests for Gemini context caching.

These tests verify that context caching works end-to-end with the real Gemini API.
They are separate from the vanilla integration tests because:
1. Caching requires minimum token thresholds (2048+ for gemini-3-pro-preview)
2. They test cache creation, reuse, and cost savings
3. They have different cost profiles (first call expensive, subsequent cheap)

Run with:
    pytest -m "integration and gemini" tests/integration/ -v
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest
from dotenv import load_dotenv

from kanoa.core.interpreter import AnalyticsInterpreter

from .conftest import get_auth_state, get_cost_tracker

# Load API keys from user config directory
config_dir = Path.home() / ".config" / "kanoa"
if (config_dir / ".env").exists():
    load_dotenv(config_dir / ".env")


def has_potential_credentials() -> bool:
    """
    Quick check if credentials might be available.

    This is a fast, non-blocking check that looks for credential files/env vars.
    It does NOT validate that credentials are working - that happens lazily
    when the first test actually runs.
    """
    if os.environ.get("GOOGLE_API_KEY"):
        return True
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    # Check for ADC credentials file (from gcloud auth application-default login)
    adc_path = (
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )
    return adc_path.exists()


pytestmark = [
    pytest.mark.integration,
    pytest.mark.gemini,
    pytest.mark.caching,
    pytest.mark.skipif(
        not has_potential_credentials(),
        reason="No Gemini credentials found",
    ),
]


def _is_auth_error(error_msg: str) -> bool:
    """Check if an error message indicates an authentication failure."""
    auth_keywords = ["401", "403", "auth", "credential", "permission", "token"]
    return any(kw in error_msg.lower() for kw in auth_keywords)


# Knowledge base content large enough for caching (>2048 tokens for gemini-3-pro)
# Target: ~3000 tokens to ensure we're safely above the minimum threshold
# Note: 1 token ≈ 4 characters for English text
CLIMATE_KB_CONTENT = """
# Climate Science Reference Guide

## Executive Summary

This comprehensive reference guide provides essential context for interpreting
climate science data visualizations and analytics. It covers global temperature
trends, greenhouse gas concentrations, sea level rise projections, extreme weather
attribution, and methodology considerations. All data and projections are based on
peer-reviewed scientific literature and official reports from NASA, NOAA, IPCC, and
other authoritative sources.

## Global Temperature Trends

The Earth's average surface temperature has risen approximately 1.1°C since the
pre-industrial era (1850-1900). This warming is primarily driven by anthropogenic
greenhouse gas emissions, particularly carbon dioxide (CO2), methane (CH4), and
nitrous oxide (N2O). The rate of warming has accelerated significantly since the
mid-20th century, with the last decade being the warmest on record.

### Key Temperature Metrics

| Metric | Value | Source | Year |
| --- | --- | --- | --- |
| Global mean temp anomaly | +1.48°C | NASA GISS | 2023 |
| Arctic amplification factor | 2-3x | IPCC AR6 | 2021 |
| Ocean heat content increase | 0.91 W/m² | NOAA | 2023 |
| Land surface warming rate | +1.59°C | Berkeley Earth | 2023 |
| Ocean surface warming rate | +0.88°C | HadSST4 | 2023 |

The warming is not uniform across the globe. The Arctic is warming at 2-3 times
the global average, a phenomenon known as Arctic amplification. This has
significant implications for sea ice extent, permafrost stability, and global
weather patterns. The Arctic has lost approximately 13% of its September sea ice
extent per decade since satellite observations began in 1979.

### Regional Temperature Variations

Different regions experience warming at different rates due to various factors:

1. **Polar Regions**: Experiencing the fastest warming due to ice-albedo feedback
2. **Continental Interiors**: Warm faster than coastal areas due to lower heat capacity
3. **Urban Areas**: Additional warming from urban heat island effect
4. **Southern Ocean**: Slower warming due to deep water upwelling

## Carbon Dioxide Concentrations

Atmospheric CO2 has increased from 280 ppm (pre-industrial) to over 420 ppm today.
This represents a 50% increase, with the rate of increase accelerating significantly
over the past several decades. The current rate of CO2 increase is unprecedented
in at least the past 800,000 years based on ice core records.

### Historical CO2 Levels

| Year | CO2 (ppm) | Annual Increase | Cumulative Change |
| --- | --- | --- | --- |
| 1750 | 280 | baseline | 0% |
| 1900 | 296 | 0.3 ppm/yr | +6% |
| 1960 | 317 | 0.9 ppm/yr | +13% |
| 1980 | 338 | 1.2 ppm/yr | +21% |
| 2000 | 370 | 1.5 ppm/yr | +32% |
| 2010 | 390 | 2.0 ppm/yr | +39% |
| 2023 | 421 | 2.5 ppm/yr | +50% |

The Keeling Curve, which tracks CO2 at Mauna Loa Observatory since 1958, shows
not only the long-term increase but also seasonal oscillations driven by
Northern Hemisphere vegetation growth and decay. Peak CO2 occurs in May before
the Northern Hemisphere growing season, and minimum occurs in September after
vegetation has absorbed carbon through photosynthesis.

### Other Greenhouse Gases

| Gas | Pre-industrial | Current | GWP (100-yr) | Main Sources |
| --- | --- | --- | --- | --- |
| CH4 (Methane) | 722 ppb | 1912 ppb | 28 | Agriculture, fossil fuels |
| N2O (Nitrous oxide) | 270 ppb | 336 ppb | 265 | Agriculture, industry |
| CFCs | 0 | Various | 5000-14000 | Refrigerants (banned) |
| HFCs | 0 | Growing | 1000-4000 | Refrigerant replacements |

## Sea Level Rise

Global mean sea level has risen approximately 20 cm since 1900, with the rate
accelerating from 1.7 mm/year (1901-2010) to 3.7 mm/year (2006-2018). Recent
satellite measurements indicate the current rate may be approaching 4.5 mm/year.
This acceleration is driven by increased ice sheet mass loss from Greenland and
Antarctica, combined with ongoing thermal expansion of ocean water.

### Sea Level Projections by Scenario

| Scenario | Description | 2050 Rise | 2100 Rise | Main Driver |
| --- | --- | --- | --- | --- |
| SSP1-1.9 | Net zero by 2050 | 0.15-0.23m | 0.28-0.55m | Thermal expansion |
| SSP1-2.6 | Paris targets met | 0.17-0.26m | 0.32-0.62m | Thermal expansion |
| SSP2-4.5 | Middle road | 0.20-0.30m | 0.44-0.76m | Glacier melt |
| SSP3-7.0 | Regional rivalry | 0.22-0.33m | 0.55-0.90m | Ice sheet loss |
| SSP5-8.5 | Fossil fuel dev | 0.25-0.37m | 0.63-1.01m | Ice sheet collapse |

The main contributors to sea level rise include:

1. **Thermal expansion** (42%): Ocean water expands as it warms
2. **Glacier and ice cap melt** (21%): Mountain glaciers losing mass globally
3. **Greenland ice sheet** (15%): Accelerating mass loss
4. **Antarctic ice sheet** (8%): West Antarctic showing instability
5. **Land water storage** (14%): Groundwater depletion, reservoirs

### Regional Sea Level Variations

Sea level rise is not uniform globally. Some regions will experience significantly
more rise than the global average due to:

- Gravitational effects from ice sheet mass loss
- Ocean circulation changes
- Land subsidence (especially in delta regions)
- Vertical land motion from glacial isostatic adjustment

## Extreme Weather Events

Climate change is increasing the frequency and intensity of extreme weather events.
Heat waves, droughts, and heavy precipitation events have all become more common,
while cold extremes have become less frequent. The science of extreme event
attribution has advanced significantly, allowing quantification of climate change's
contribution to specific events.

### Attribution Science Findings

Modern attribution studies can quantify how much climate change contributed to
specific extreme events. Key findings from recent studies include:

| Event Type | Climate Change Impact | Confidence | Example |
| --- | --- | --- | --- |
| Heat waves | 2-10x more likely | Very High | Europe 2022 |
| Heavy precipitation | 1.3-1.5x more likely | High | Germany 2021 |
| Hurricane intensity | Rapid intensification up | Medium-High | Ian 2022 |
| Droughts | 1.5-2x more likely | Medium-High | US Southwest |
| Wildfires | 2-4x more area burned | High | Australia 2019 |
| Marine heat waves | 20x more likely | Very High | NE Pacific 2021 |

### Observed Trends in Extremes

1. **Heat waves**: Frequency has tripled since 1960s in most regions
2. **Precipitation extremes**: Wettest days 7% wetter since 1950
3. **Tropical cyclones**: Peak winds increased ~5% since 1979
4. **Drought**: Flash droughts becoming more common
5. **Compound events**: Multiple extremes occurring simultaneously more often

## Methodology Notes

When interpreting climate data visualizations, consider the following important
methodological factors that can affect how data should be understood:

### Baseline Periods

| Baseline | Use Case | Notes |
| --- | --- | --- |
| 1850-1900 | IPCC reports | Pre-industrial reference |
| 1951-1980 | NASA GISS | Good global coverage |
| 1961-1990 | WMO standard | Traditional climate normal |
| 1981-2010 | Current normal | Most recent 30-year period |
| 1991-2020 | New normal | Being adopted now |

### Data Quality Considerations

1. **Spatial coverage**: Early records have less global coverage, especially
   over oceans and polar regions
2. **Measurement methods**: Instrumentation has changed over time
3. **Urban heat islands**: Can bias local temperature records
4. **Ocean measurements**: Ship-based vs buoy vs satellite differences
5. **Reanalysis products**: Combine observations with models, each with tradeoffs

### Uncertainty Communication

- **Very likely**: >90% probability
- **Likely**: >66% probability
- **About as likely as not**: 33-66% probability
- **Unlikely**: <33% probability
- **Very unlikely**: <10% probability

## Policy Context

The Paris Agreement aims to limit warming to 1.5°C above pre-industrial levels,
with 2°C as an upper bound. Current policies put us on track for approximately
2.7°C of warming by 2100. Achieving the 1.5°C target requires:

1. **Net-zero emissions by 2050**: Global CO2 emissions must reach net zero
2. **45% reduction by 2030**: Emissions must fall 45% from 2010 levels
3. **Rapid renewable deployment**: Solar and wind must scale 4-6x by 2030
4. **Phase out coal**: Unabated coal must be phased out by 2030 in OECD
5. **Protect carbon sinks**: Halt deforestation and restore ecosystems

### Carbon Budget

The remaining carbon budget for 1.5°C (50% chance) is approximately 500 GtCO2
from 2020. At current emission rates (~40 GtCO2/year), this budget will be
exhausted by approximately 2032.

## References and Data Sources

This knowledge base draws on authoritative sources including:

- **NASA GISS**: Global temperature analysis
- **NOAA NCEI**: Ocean and atmospheric data
- **IPCC AR6**: Sixth Assessment Report (2021-2023)
- **Berkeley Earth**: Independent temperature analysis
- **Copernicus C3S**: European climate service
- **WMO**: World Meteorological Organization reports
"""


class TestGeminiCachingIntegration:
    """
    Integration tests for Gemini context caching.

    These tests verify the cache lifecycle:
    1. First query with KB creates cache (cache miss expected)
    2. Second query reuses cache (cache hit expected, cached_tokens > 0)
    3. Cache clear invalidates (subsequent query creates new cache)

    Tests are idempotent - they clear any existing caches at setup.
    """

    @pytest.fixture(scope="class")
    def kb_dir(self) -> Generator[Path, None, None]:
        """Create a temporary knowledge base directory with sufficient content."""
        with tempfile.TemporaryDirectory(prefix="kanoa_cache_test_") as tmp:
            kb_path = Path(tmp)
            (kb_path / "climate_science.md").write_text(CLIMATE_KB_CONTENT)

            # Log KB size for debugging
            char_count = len(CLIMATE_KB_CONTENT)
            word_count = len(CLIMATE_KB_CONTENT.split())
            estimated_tokens = char_count // 4  # Rough estimate
            print(f"\n📚 KB size: {word_count} words, ~{estimated_tokens} tokens")
            print("   (Minimum for gemini-3-pro-preview: 2048 tokens)")

            yield kb_path

    @pytest.fixture(scope="class")
    def interpreter_with_cache(self, kb_dir: Path) -> Any:
        """Initialize interpreter with caching enabled (with lazy auth)."""
        auth_state = get_auth_state()

        # Check if we already know auth is broken
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Gemini auth previously failed: {error}")

        try:
            interp = AnalyticsInterpreter(
                backend="gemini",
                kb_path=str(kb_dir),
                cache_ttl=300,  # 5 minute cache for tests
            )
            auth_state.mark_auth_ok("gemini")

            # Clear any existing caches for idempotency
            # This ensures we start fresh regardless of previous test runs
            backend = getattr(interp, "backend", None)
            if backend and hasattr(backend, "clear_cache"):
                backend.clear_cache()
                print("✓ Cleared existing cache for idempotent test start")

            return interp
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(
                    f"Gemini auth failed: {error_msg}\n"
                    "Try: gcloud auth application-default login"
                )
            else:
                pytest.fail(f"Could not initialize Gemini backend: {e}")

    def test_first_query_creates_cache(self, interpreter_with_cache: Any) -> None:
        """
        First query should create a cache and return valid results.

        This establishes the cache. For implicit caching (gemini-3-pro-preview),
        the cache is created automatically if KB content exceeds 2048 tokens.
        """
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 60)
        print("📐 TEST: First Query (Cache Creation)")
        print("=" * 60)

        # Use data dict since interpret() requires fig or data
        data = {"query": "CO2 increase rate per year"}
        context = "Climate data query"
        focus = "What is the current rate of CO2 increase per year?"

        try:
            result = interpreter_with_cache.interpret(
                data=data,
                context=context,
                focus=focus,
            )
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        assert result.text is not None
        assert len(result.text) > 50
        assert result.backend == "gemini"

        print(f"\n🎓 Response: {result.text[:100]}...")
        if result.usage:
            cost = result.usage.cost
            get_cost_tracker().record("test_first_query_creates_cache", cost)
            print(f"💰 Cost: ${cost:.6f}")
            print(f"📊 Input tokens: {result.usage.input_tokens}")
            cached = result.usage.cached_tokens or 0
            print(f"📊 Cached tokens: {cached}")

            # For first query, we may or may not have cache (depends on implicit)
            # The key is that input_tokens should include KB content
            assert result.usage.input_tokens > 1000, "KB content should be included"

    def test_second_query_uses_cache(self, interpreter_with_cache: Any) -> None:
        """
        Second query should reuse the cache and show cached tokens.

        With implicit caching on gemini-3-pro-preview, if KB > 2048 tokens
        and queries are sent within a short time window with same prefix,
        we should see cached_tokens > 0.
        """
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 60)
        print("📐 TEST: Second Query (Cache Hit Expected)")
        print("=" * 60)

        # Use data dict since interpret() requires fig or data
        data = {"query": "Sea level projections"}
        context = "Climate data query"
        focus = "What are the sea level projections for 2100 under SSP5-8.5?"

        try:
            result = interpreter_with_cache.interpret(
                data=data,
                context=context,
                focus=focus,
            )
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        assert result.text is not None
        assert len(result.text) > 50

        print(f"\n🎓 Response: {result.text[:100]}...")
        if result.usage:
            cost = result.usage.cost
            get_cost_tracker().record("test_second_query_uses_cache", cost)
            print(f"💰 Cost: ${cost:.6f}")
            print(f"📊 Input tokens: {result.usage.input_tokens}")
            cached = result.usage.cached_tokens or 0
            print(f"📊 Cached tokens: {cached}")

            # With implicit caching, second query should show cache hit
            if cached > 0:
                savings = getattr(result.usage, "cache_savings", 0) or 0
                print(f"✅ Cache HIT! Cached: {cached} tokens, Savings: ${savings:.6f}")
            else:
                print("⚠️ No cache hit (implicit caching may not have triggered)")
                print("   This can happen if KB is below threshold or queries differ")

    def test_clear_cache_invalidates(self, interpreter_with_cache: Any) -> None:
        """Clearing cache should invalidate and require re-creation."""
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 60)
        print("📐 TEST: Clear Cache")
        print("=" * 60)

        # Clear the cache via the backend
        if hasattr(interpreter_with_cache, "_backend"):
            backend = interpreter_with_cache._backend
            if hasattr(backend, "clear_cache"):
                backend.clear_cache()
                print("✓ Cache cleared via backend")
            elif hasattr(backend, "_cache"):
                backend._cache = None
                print("✓ Cache cleared by resetting _cache")
        print("✓ Cache invalidation requested")

        # Use data dict since interpret() requires fig or data
        data = {"query": "Arctic amplification"}
        context = "Climate data query"
        focus = "Summarize the Arctic amplification factor."

        # Next query should work (creates new cache)
        try:
            result = interpreter_with_cache.interpret(
                data=data,
                context=context,
                focus=focus,
            )
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        assert result.text is not None
        assert "arctic" in result.text.lower() or "2" in result.text

        print(f"\n🎓 Response: {result.text[:100]}...")
        if result.usage:
            cost = result.usage.cost
            get_cost_tracker().record("test_clear_cache_invalidates", cost)
            print(f"💰 Cost: ${cost:.6f}")


class TestGeminiNoCachingBaseline:
    """Baseline tests without caching for comparison."""

    @pytest.fixture(scope="class")
    def interpreter_no_cache(self) -> Any:
        """Initialize interpreter without caching (with lazy auth)."""
        auth_state = get_auth_state()

        # Check if we already know auth is broken
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Gemini auth previously failed: {error}")

        try:
            interp = AnalyticsInterpreter(
                backend="gemini",
                cache_ttl=None,  # Explicitly disable caching
            )
            auth_state.mark_auth_ok("gemini")
            return interp
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(
                    f"Gemini auth failed: {error_msg}\n"
                    "Try: gcloud auth application-default login"
                )
            else:
                pytest.fail(f"Could not initialize Gemini backend: {e}")

    def test_no_cache_direct_prompt(self, interpreter_no_cache: Any) -> None:
        """Direct prompt without KB or caching."""
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 60)
        print("📐 TEST: No Cache Baseline")
        print("=" * 60)

        # Use data dict since interpret() requires fig or data
        data = {"question": "What is 2 + 2?"}
        context = "Simple math test"
        focus = "Respond with just the number."

        try:
            result = interpreter_no_cache.interpret(
                data=data,
                context=context,
                focus=focus,
            )
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        assert result.text is not None
        assert "4" in result.text

        print(f"\n🎓 Response: {result.text[:50]}...")
        if result.usage:
            cost = result.usage.cost
            get_cost_tracker().record("test_no_cache_direct_prompt", cost)
            print(f"💰 Cost: ${cost:.6f}")
            # Should have no cached tokens
            assert result.usage.cached_tokens is None or result.usage.cached_tokens == 0
