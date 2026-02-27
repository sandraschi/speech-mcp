# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: (SOTA Modular) |

## Vocal Social Engineering & Ethical Guardrails

As of **February 27, 2026 (v0.2.1)**, Speech-MCP implements a **Security Bastion** to mitigate the risks of highly expressive synthetic speech:

1.  **Intent Validation**: The `validate_speech_intent` tool MUST be called before any synthesis of emotional or impersonated speech. It checks for known social engineering patterns (e.g., "urgent money transfers").
2.  **Forensic Auditing**: Every high-intensity emotional speech generation is logged via `log_speech_audit`, creating a forensic trace for identifying malicious usage. This feature was integrated following the **Feb 19, 2026** SOTA model releases.
3.  **Watermarking**: We recommend third-party audio watermarking for all production endpoints.

## Reporting a Vulnerability

Please report vulnerabilities by opening an issue or contacting the maintainers directly. As this is a beta project, we aim to address security concerns with high priority.
