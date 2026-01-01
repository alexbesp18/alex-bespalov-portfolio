# Security Policy

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it by emailing the maintainer directly.

### What to Include

- Type of issue (e.g., credential exposure, injection, etc.)
- Location of the affected source code (file and line number)
- Steps to reproduce the issue
- Potential impact of the vulnerability

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Depends on severity and complexity

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Security Best Practices

When using this project:

1. **Never commit `.env` files** - Use `.env.example` as a template
2. **Rotate API keys regularly** - Especially if exposed accidentally
3. **Use environment variables** - Never hardcode secrets in source code
4. **Review dependencies** - Keep packages updated via Dependabot alerts
