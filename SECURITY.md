# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by opening a new [GitHub security
advisory](https://github.com/lhzn-io/kanoa/security/advisories/new).

You can also send an email to [security@lhzn.io](mailto:security@lhzn.io).

If the security vulnerability is accepted, a patch will be crafted privately
in order to prepare a dedicated bugfix release as timely as possible (depending
on the complexity of the fix).

## Security Considerations

`kanoa` is a client library that interfaces with third-party LLM providers (Gemini, Claude, OpenAI, vLLM). The security posture of your application depends on:

1. **Backend Provider Security**: kanoa cannot mitigate vulnerabilities in the underlying LLM services (e.g., prompt injection, data exfiltration). Users should review the security documentation of their chosen provider.

2. **API Key Management**: Protect your API keys as you would any credential. See the [Authentication Guide](./docs/source/user_guide/authentication.md) for best practices.

3. **Input Validation**: If you build applications that accept user-generated content for interpretation, implement appropriate input validation and sanitization.

kanoa security reports should focus on vulnerabilities in the library itself (e.g., code execution, dependency vulnerabilities, API key leakage in logs).
