# Climate Science Knowledge Base

This knowledge base provides context for interpreting climate and ocean
science visualizations.

## Contents

- `climate_methodology.md` - Standard methodologies for climate data analysis
- `ocean_temperature.md` - Sea surface temperature analysis context
- `co2_emissions.md` - CO2 concentration and emissions research context

## Usage

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    kb_path='./climate_science_kb',
    kb_type='text'
)
```

## Sources

The content is synthesized from public domain climate science literature
including IPCC reports and NOAA methodologies.
