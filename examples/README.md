# kanoa Examples

This directory contains example notebooks and scripts demonstrating kanoa's capabilities.

## Available Examples

### quickstart_10min.ipynb

10 Minutes to kanoa - Comprehensive Introduction

This notebook showcases kanoa's core capabilities:

1. **Multi-Backend Support**
   - Gemini (Google) - with native PDF vision
   - Claude (Anthropic) - text-based analysis
   - Molmo (Local) - privacy-preserving inference

2. **Knowledge Base Integration**
   - Text/Markdown knowledge bases
   - PDF document processing (Gemini)
   - Context-aware interpretations

3. **Visualization Analysis**
   - Matplotlib figure interpretation
   - Multi-panel dashboard analysis
   - Complex statistical visualizations

4. **Data Interpretation**
   - DataFrame analysis
   - Tabular data insights
   - Statistical summaries

5. **Cost Tracking**
   - Token usage monitoring
   - Cost comparison across backends
   - Optimization insights

**Prerequisites:**

- `conda activate kanoa` (or your environment)
- Set `GOOGLE_API_KEY` for Gemini backend
- Optional: Set `ANTHROPIC_API_KEY` for Claude backend

**Quick Start:**

```bash
jupyter notebook examples/quickstart_10min.ipynb
```

To verify kanoa is installed correctly, you can run:

```bash
python -c "from kanoa import AnalyticsInterpreter; print('✓ kanoa installed successfully')"
```

---

## Running the Quickstart

### Option 1: Jupyter Notebook

```bash
# Activate environment
conda activate kanoa

# Start Jupyter
jupyter notebook

# Navigate to examples/ and open quickstart_10min.ipynb
```

### Option 2: JupyterLab

```bash
# Activate environment
conda activate kanoa

# Start JupyterLab
jupyter lab

# Navigate to examples/ and open quickstart_10min.ipynb
```

### Option 3: VS Code

1. Open the `kanoa` repository in VS Code
2. Install the Jupyter extension
3. Open `examples/quickstart_10min.ipynb`
4. Select the `kanoa` kernel
5. Run cells interactively

---

## API Keys

The examples require API keys for cloud backends:

### Gemini (Required for most examples)

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Get your key at: <https://aistudio.google.com/apikey>

### Claude (Optional)

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Get your key at: <https://console.anthropic.com/>

### Molmo (Local - No API Key Required)

Molmo runs locally and requires no API key, but may need additional model setup.

---

## Cost Estimates

Based on typical usage in the demo notebook:

| Backend | Approximate Cost per Run |
|---------|--------------------------|
| Gemini  | $0.01 - $0.05            |
| Claude  | $0.02 - $0.08            |
| Molmo   | $0.00 (local)            |

*Actual costs depend on input size and response length.*

---

## Troubleshooting

### "Module not found: kanoa"

Make sure you've installed kanoa in development mode:

```bash
pip install -e .
```

### "API key not found"

Set the appropriate environment variable before running:

```bash
export GOOGLE_API_KEY="your-key"
```

### Jupyter kernel issues

Ensure the kernel matches your environment:

```bash
python -m ipykernel install --user --name=kanoa
```

---

## Contributing Examples

Have a cool use case? We'd love to see it! Please:

1. Create a new notebook in `examples/`
2. Follow the naming convention: `{feature}_{use_case}.ipynb`
3. Include clear markdown explanations
4. Add it to this README
5. Submit a PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Next Steps

After exploring the quickstart, check out:

- [User Guide](../docs/source/user_guide/index.md) - Detailed usage documentation
- [API Reference](../docs/source/api/index.md) - Complete API documentation
- [Backends Guide](../docs/source/user_guide/backends.md) - Backend-specific features

---

*For questions or issues, please [open an issue](https://github.com/lhzn-io/kanoa/issues).*
