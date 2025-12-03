# Authentication & API Key Management

kanoa supports multiple authentication methods depending on your backend and environment. This guide covers everything from quick setup to production deployment and security best practices.

## Quick Setup

### Environment Variables (Recommended)

The simplest and most secure way to manage API keys:

```bash
# Gemini (Google) - Get at https://aistudio.google.com/apikey
export GOOGLE_API_KEY="your-google-api-key"

# Claude (Anthropic) - Get at https://console.anthropic.com/
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Molmo (Local) - No API key needed!
# Models stored in ~/.cache/kanoa/models/molmo/ by default
export MOLMO_MODEL_PATH="$HOME/.cache/kanoa/models/molmo"  # Optional override
```

### Using `.env` Files (Local Development)

⚠️ **Security Note**: API keys generate costs for you or your organization. Protect them carefully to avoid unauthorized usage and unexpected charges.

#### Option 1: User Config Directory (Recommended)

Store `.env` outside the repository for maximum security:

```bash
# Create user config directory
mkdir -p ~/.config/kanoa

# Create .env file
cat > ~/.config/kanoa/.env << EOF
GOOGLE_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
EOF
```

Load in your code:

```python
from pathlib import Path
from dotenv import load_dotenv

# Load from user config
config_dir = Path.home() / ".config" / "kanoa"
load_dotenv(config_dir / ".env")

from kanoa import AnalyticsInterpreter
interpreter = AnalyticsInterpreter(backend='gemini')
```

#### Option 2: Repo Root with Pre-commit Protection

For integration tests and CI/CD, you can use repo-root `.env`:

```bash
# Create .env in repo root (already in .gitignore)
echo "GOOGLE_API_KEY=your-key" > .env
echo "ANTHROPIC_API_KEY=your-key" >> .env
```

Load in your code:

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env from current directory

from kanoa import AnalyticsInterpreter
interpreter = AnalyticsInterpreter(backend='gemini')
```

The `.env` file is in `.gitignore`, and we use `detect-secrets` pre-commit hook as backup protection.

kanoa backends automatically detect environment variables, so you don't need to pass keys explicitly.

---

## Backend-Specific Authentication

### Gemini (Google)

#### Local Development

##### Option 1: API Key (Simplest)

```bash
export GOOGLE_API_KEY="your-api-key"
```

Then in Python:

```python
interpreter = AnalyticsInterpreter(backend='gemini')
# Automatically uses GOOGLE_API_KEY
```

##### Option 2: Application Default Credentials (ADC)

For Google Cloud projects:

```bash
gcloud auth application-default login
```

Then in Python:

```python
interpreter = AnalyticsInterpreter(backend='gemini')
# Automatically uses ADC
```

> **Note for Contributors**: Integration tests can use ADC instead of API keys. Just run `gcloud auth application-default login` before running tests.

#### Production / CI/CD

##### Service Account with Workload Identity Federation (Recommended)

1. Create a Service Account with `roles/aiplatform.user`
2. Configure Workload Identity Federation for GitHub Actions
3. Use the `google-github-actions/auth` action

##### Service Account Key (Less Secure)

1. Create a Service Account
2. Generate a JSON key
3. Store as GitHub Secret
4. Set `GOOGLE_APPLICATION_CREDENTIALS` in CI

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}
```

### Claude (Anthropic)

#### Local Development

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or in Python:

```python
interpreter = AnalyticsInterpreter(
    backend='claude',
    api_key='your-api-key'  # Optional if env var is set
)
```

#### Production / CI/CD

Store the API key as a GitHub Secret:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Molmo (Local Inference)

Molmo runs entirely locally - **no API key required**!

#### Default Model Location

kanoa stores Molmo models in:

```bash
~/.cache/kanoa/models/molmo/
```

This follows the XDG Base Directory Specification, consistent with Hugging Face and other tools.

#### Download Model

##### Option 1: Download to default location (recommended)

```bash
# Set the default XDG-compliant path
export MOLMO_MODEL_PATH="$HOME/.cache/kanoa/models/molmo"

# 1. Install CLI
pip install huggingface_hub

# 2. Login (Required for gated models like Molmo)
# Get token at: https://huggingface.co/settings/tokens
huggingface-cli login

# 3. Download model
huggingface-cli download allenai/Molmo-7B-D-0924 --local-dir "$MOLMO_MODEL_PATH"
```

##### Option 2: Custom location

```bash
# Set custom path
export MOLMO_MODEL_PATH="/path/to/your/models"

# Download to custom location
huggingface-cli download allenai/Molmo-7B-D-0924 --local-dir "$MOLMO_MODEL_PATH"
```

##### Option 3: Using Python

```python
from huggingface_hub import snapshot_download
from pathlib import Path

# Download to default XDG location
model_path = Path.home() / ".cache" / "kanoa" / "models" / "molmo"
snapshot_download(repo_id="allenai/Molmo-7B-D", local_dir=str(model_path))
```

#### Environment Variables

- `MOLMO_MODEL_PATH`: Override default model directory (optional)
- `XDG_CACHE_HOME`: Change XDG cache root (defaults to `~/.cache`)

#### Requirements

- Python 3.11+
- PyTorch (install for your hardware)
- GPU recommended (but CPU works)

⚠️ **Disk Space**: Molmo-7B requires ~14GB

---

## Production Deployment

### Cloud Secret Management

For production deployments, use dedicated secret management services:

#### Google Cloud Secret Manager (Recommended for Gemini)

```python
from google.cloud import secretmanager

def get_api_key(project_id: str, secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Use in kanoa
api_key = get_api_key("my-project", "gemini-api-key")
interpreter = AnalyticsInterpreter(backend='gemini', api_key=api_key)
```

#### AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Use in kanoa
secrets = get_secret("kanoa-api-keys")
interpreter = AnalyticsInterpreter(
    backend='claude',
    api_key=secrets['anthropic_api_key']
)
```

#### HashiCorp Vault

```python
import hvac

client = hvac.Client(url='http://localhost:8200')
client.token = 'your-vault-token'

# Read secret
secret = client.secrets.kv.v2.read_secret_version(path='kanoa/api-keys')
api_key = secret['data']['data']['google_api_key']

interpreter = AnalyticsInterpreter(backend='gemini', api_key=api_key)
```

---

## Security Best Practices

### Core Principles

1. **Never hardcode API keys** in source code
2. **Use environment variables** for local development
3. **Leverage secret management services** for production
4. **Implement least privilege** access control
5. **Regular key rotation** and monitoring

### Key Rotation

Rotate API keys regularly (every 90 days recommended):

```bash
# 1. Generate new key from provider console
# 2. Update environment variable or secret manager
# 3. Test with new key
# 4. Revoke old key
```

### Monitoring

Monitor API usage for unusual patterns:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(backend='gemini', track_costs=True)

# After using
costs = interpreter.get_cost_summary()
print(f"Total cost: ${costs['total_cost_usd']:.4f}")
print(f"Total calls: {costs['total_calls']}")
```

### Least Privilege

Use separate API keys for:

- Development
- Staging
- Production
- CI/CD pipelines

### Never Expose Client-Side

⚠️ **Never** include API keys in:

- Frontend JavaScript
- Mobile apps
- Public repositories
- Docker images (use secrets injection)

---

## Troubleshooting

### "API key not found"

```bash
# Check if environment variable is set
echo $GOOGLE_API_KEY

# If empty, set it
export GOOGLE_API_KEY="your-key"

# Or use .env file
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GOOGLE_API_KEY'))"
```

### "Invalid API key"

1. Verify key is correct (copy-paste from console)
2. Check for extra whitespace
3. Ensure key hasn't been revoked
4. Verify billing is enabled (for cloud providers)

### "Permission denied"

Ensure your Service Account has the correct roles:

- Gemini: `roles/aiplatform.user`
- Vertex AI: `roles/aiplatform.user` + `roles/storage.objectViewer` (for PDFs)

### "Your default credentials were not found"

Run:

```bash
gcloud auth application-default login
```

---

## For Contributors

### Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/lhzn-io/kanoa.git
   cd kanoa
   ```

2. **Create `.env` file** (not tracked in git):

   ```bash
   # .env
   GOOGLE_API_KEY=your-google-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   # Molmo models stored in ~/.cache/kanoa/models/molmo/ by default
   # MOLMO_MODEL_PATH=/custom/path  # Optional override
   ```

3. **Install development dependencies**:

   ```bash
   pip install -e .[dev]
   ```

4. **Run integration tests**:

   ```bash
   # Test Gemini
   pytest -m gemini tests/integration/test_gemini_integration.py

   # Test Claude
   pytest -m claude tests/integration/test_claude_integration.py

   # Test Molmo (requires local model)
   pytest -m molmo tests/integration/test_molmo_integration.py
   ```

### Contributing Guidelines

When contributing to kanoa:

1. ✅ **DO**: Use environment variables or `.env` files
2. ✅ **DO**: Add `.env` and `.secrets/` to `.gitignore`
3. ✅ **DO**: Document any new API key requirements
4. ❌ **DON'T**: Commit API keys or secrets
5. ❌ **DON'T**: Hardcode keys in examples or tests
6. ❌ **DON'T**: Include keys in screenshots or documentation

---

## References

This authentication strategy is based on best practices from:

- **LangChain**: Environment variables, secret management integration
- **OpenAI SDK**: `.env` files, never hardcode keys
- **Anthropic SDK**: `python-dotenv`, GitHub secret scanning
- **Google Cloud**: Secret Manager, ADC (Application Default Credentials)
