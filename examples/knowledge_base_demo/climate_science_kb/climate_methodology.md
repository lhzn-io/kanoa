# Climate Data Analysis Methodology

## Time Series Analysis Standards

### Baseline Periods

Standard baseline periods for climate anomaly calculations:

- **1951-1980 baseline**: Used by NASA GISS for global temperature anomalies
- **1961-1990 baseline**: WMO standard reference period
- **1981-2010 baseline**: Current WMO climatological normal period

### Statistical Methods

#### Linear Trend Analysis

- Ordinary Least Squares (OLS) regression for trend estimation
- Mann-Kendall test for trend significance
- Sen's slope estimator for robust trend magnitude

#### Uncertainty Quantification

- 95% confidence intervals for trend slopes
- Standard error of the mean for anomalies
- Combined uncertainty from measurement and sampling

### Smoothing Techniques

- **5-year running mean**: Reduces interannual variability
- **LOWESS smoothing**: Locally weighted regression
- **11-year running mean**: Filters solar cycle variability

## Anomaly Calculations

Temperature anomalies are calculated as:

```text
Anomaly = Observed Value - Baseline Mean
```

where Baseline Mean is the average for the reference period.

### Interpreting Anomalies

| Anomaly Range | Interpretation               |
| ------------- | ---------------------------- |
| < -0.5°C      | Significantly below normal   |
| -0.5 to 0°C   | Below normal                 |
| 0 to 0.5°C    | Above normal                 |
| 0.5 to 1.0°C  | Significantly above normal   |
| > 1.0°C       | Exceptionally above normal   |

## Data Quality Standards

### Missing Data Handling

- Maximum 20% missing data per time series
- Linear interpolation for gaps < 3 consecutive points
- Flag but exclude longer gaps from trend calculations

### Spatial Coverage

- Global mean requires >80% spatial coverage
- Land-only and ocean-only indices calculated separately
- Area-weighted averaging for global indices
