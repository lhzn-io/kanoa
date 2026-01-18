# Testing GitHub Copilot Backend Locally

This guide explains how to configure, authenticate, and test the GitHub Copilot backend.

## Prerequisites

Before testing the GitHub Copilot backend, you need:

1. **GitHub Copilot Subscription**
   - Individual ($10/month)
   - Business ($19/user/month)  
   - Enterprise (custom pricing)
   
   Sign up at: https://github.com/features/copilot

2. **GitHub CLI (gh)**
   - Required for authentication
   - Install from: https://cli.github.com/

3. **GitHub Copilot CLI Extension**
   - Installed via GitHub CLI
   - Provides the `copilot` command

## Installation Steps

### 1. Install GitHub CLI

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Fedora/CentOS/RHEL
sudo dnf install gh
```

**Windows:**
```powershell
winget install --id GitHub.cli
```

### 2. Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts to authenticate:
- Choose "GitHub.com"
- Choose "HTTPS" or "SSH" (HTTPS recommended)
- Authenticate via web browser

Verify authentication:
```bash
gh auth status
```

You should see: "✓ Logged in to github.com as <your-username>"

### 3. Install GitHub Copilot CLI Extension

```bash
gh extension install github/gh-copilot
```

Verify installation:
```bash
copilot --version
```

### 4. Install kanoa with GitHub Copilot Support

```bash
pip install kanoa[github-copilot]
```

Or for development:
```bash
cd /path/to/kanoa
pip install -e ".[dev]"
```

## Configuration

### Environment Variables (Optional)

You can customize the Copilot CLI path if needed:

```bash
export COPILOT_CLI_PATH=/custom/path/to/copilot
```

### Using Custom CLI Server (Optional)

If running an external Copilot CLI server:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend='github-copilot',
    cli_url='localhost:8080',  # Connect to external server
    model='gpt-5'
)
```

## Testing

### Unit Tests (No Credentials Required)

Unit tests use mocked SDK and don't require authentication:

```bash
# Run GitHub Copilot unit tests
pytest tests/unit/test_github_copilot_backend.py -v

# Expected output: 9 passed
```

### Integration Tests (Requires Authentication)

Integration tests make real API calls and require proper setup:

```bash
# Run GitHub Copilot integration tests
pytest tests/integration/test_github_copilot_integration.py -v

# Or run with the github_copilot marker
pytest -m github_copilot -v
```

**Important Notes:**
- Integration tests are automatically skipped if credentials aren't configured
- Tests include rate limiting (5 min between runs, max 20 runs/day)
- Override with: `pytest --force-integration` or `export KANOA_SKIP_RATE_LIMIT=1`

### Manual Testing

Create a test script (`test_copilot_manual.py`):

```python
import matplotlib.pyplot as plt
import numpy as np
from kanoa import AnalyticsInterpreter

# Initialize backend
print("Initializing GitHub Copilot backend...")
interpreter = AnalyticsInterpreter(
    backend='github-copilot',
    model='gpt-5',
    verbose=1  # Enable logging
)

# Create test data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(8, 5))
plt.plot(x, y)
plt.title("Sine Wave Test")
plt.xlabel("X")
plt.ylabel("Y")

# Test streaming interpretation
print("\n" + "="*50)
print("Testing streaming interpretation...")
print("="*50)

for chunk in interpreter.interpret(
    fig=plt.gcf(),
    data={"x": x[:5].tolist(), "y": y[:5].tolist()},
    context="Mathematical function visualization",
    focus="Identify the function type and its properties"
):
    if chunk.type == "text":
        print(chunk.content, end="", flush=True)
    elif chunk.type == "usage":
        print(f"\n\nTokens: {chunk.usage.input_tokens} in / {chunk.usage.output_tokens} out")
        print(f"Estimated cost: ${chunk.usage.cost:.6f}")

print("\n\n✅ Test completed successfully!")
```

Run it:
```bash
python test_copilot_manual.py
```

## Troubleshooting

### Issue: "copilot: command not found"

**Solution:** Install the Copilot CLI extension:
```bash
gh extension install github/gh-copilot
```

### Issue: "Could not initialize GitHub Copilot backend"

**Possible causes:**
1. Not authenticated with GitHub CLI
   ```bash
   gh auth login
   ```

2. No active Copilot subscription
   - Visit: https://github.com/settings/copilot
   - Verify subscription is active

3. Copilot CLI not in PATH
   ```bash
   which copilot
   # If not found, add to PATH or use cli_path parameter
   ```

### Issue: Integration tests are skipped

**Reason:** Authentication not detected or credentials missing.

**Check:**
```bash
# Verify gh authentication
gh auth status

# Verify copilot CLI
copilot --version

# Run a simple copilot command
echo "Hello" | copilot explain
```

### Issue: "Session timeout after 120s"

**Cause:** Copilot CLI server not responding.

**Solutions:**
1. Restart the CLI:
   ```bash
   pkill copilot
   # Try your test again
   ```

2. Check Copilot service status:
   ```bash
   gh copilot status
   ```

3. Increase verbose logging:
   ```python
   interpreter = AnalyticsInterpreter(
       backend='github-copilot',
       verbose=2  # Debug logging
   )
   ```

## Limitations

### Current SDK Limitations

1. **Vision Support**: Limited in current SDK version
   - Text-based interpretation works well
   - Figure analysis may have reduced capability
   - Future SDK updates will improve vision support

2. **Token Counting**: Estimated, not actual
   - SDK doesn't expose real token counts yet
   - Estimates use ~4 chars per token heuristic
   - Costs are approximate

3. **CLI Dependency**: Requires Copilot CLI process
   - CLI must be installed and accessible
   - CLI manages authentication and JSON-RPC

### Workarounds

**For better figure analysis:**
- Provide data alongside the figure
- Use detailed context descriptions
- Extract key insights to text first

**Example:**
```python
# Include data with figure for better analysis
interpreter.interpret(
    fig=my_plot,
    data=df.describe().to_dict(),  # Add summary statistics
    context="Sales data showing quarterly trends",
    focus="Identify seasonality and anomalies"
)
```

## Cost Management

### Subscription-Based Pricing

GitHub Copilot uses subscription pricing, not per-token:
- Your subscription covers API usage
- Token estimates are for tracking only
- No surprise overage charges

### Best Practices

1. **Use appropriate models:**
   - `gpt-5` is the default
   - Check available models in SDK documentation

2. **Enable streaming for long responses:**
   ```python
   for chunk in interpreter.interpret(stream=True, ...):
       # Process chunks as they arrive
   ```

3. **Use knowledge bases efficiently:**
   - Text files only (PDF not yet supported)
   - Keep KB focused and relevant
   - Large KBs increase prompt size

## Getting Help

1. **Documentation:**
   - kanoa docs: https://kanoa.docs.lhzn.io
   - GitHub Copilot: https://docs.github.com/en/copilot

2. **Issues:**
   - kanoa: https://github.com/lhzn-io/kanoa/issues
   - Copilot SDK: https://github.com/github/copilot-sdk/issues

3. **Community:**
   - GitHub Discussions: https://github.com/lhzn-io/kanoa/discussions

## Quick Reference

```bash
# Setup (one-time)
brew install gh                                    # Install GitHub CLI
gh auth login                                      # Authenticate
gh extension install github/gh-copilot            # Install Copilot CLI
pip install kanoa[github-copilot]                 # Install kanoa

# Verify setup
gh auth status                                     # Check authentication
copilot --version                                  # Check CLI installation

# Run tests
pytest tests/unit/test_github_copilot_backend.py  # Unit tests
pytest tests/integration/ -m github_copilot        # Integration tests

# Use in code
python -c "from kanoa import AnalyticsInterpreter; \
           i = AnalyticsInterpreter(backend='github-copilot'); \
           print('✅ Backend initialized successfully!')"
```

## Next Steps

1. ✅ Complete setup steps above
2. ✅ Run unit tests to verify installation
3. ✅ Run integration tests to verify authentication
4. ✅ Try manual test script
5. ✅ Integrate into your workflow

Happy analyzing! 🚀
