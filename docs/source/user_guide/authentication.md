# Authentication

kanoa supports multiple authentication methods depending on your backend and environment.

## Gemini / Vertex AI

### Local Development

#### Option 1: Application Default Credentials (Recommended)

```bash
gcloud auth application-default login
```

Then in Python:

```python
interpreter = AnalyticsInterpreter(backend='gemini-3')
# Automatically uses ADC
```

#### Option 2: API Key

```bash
export GOOGLE_API_KEY="your-api-key"
```

Or in Python:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    api_key='your-api-key'
)
```

### Production / CI/CD

#### Service Account with Workload Identity Federation (Recommended)

1. Create a Service Account with `roles/aiplatform.user`
2. Configure Workload Identity Federation for GitHub Actions
3. Use the `google-github-actions/auth` action

#### Service Account Key (Less Secure)

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

## Claude

### Local Development

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or in Python:

```python
interpreter = AnalyticsInterpreter(
    backend='claude',
    api_key='your-api-key'
)
```

### Production / CI/CD

Store the API key as a GitHub Secret:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for local development
3. **Use Secrets** for CI/CD
4. **Prefer ADC** over API keys for Google Cloud
5. **Use Workload Identity** over Service Account keys when possible
6. **Rotate keys regularly**

## Troubleshooting

### "Your default credentials were not found"

Run:

```bash
gcloud auth application-default login
```

### "Invalid API key"

Check that your environment variable is set:

```bash
echo $GOOGLE_API_KEY
echo $ANTHROPIC_API_KEY
```

### "Permission denied"

Ensure your Service Account has the correct roles:

- Gemini: `roles/aiplatform.user`
- Vertex AI: `roles/aiplatform.user` + `roles/storage.objectViewer` (for PDFs)
