# Prompt Engineering: Directory & Standards

This directory contains the core Prompt Engineering specifications, guardrails, and production LLM templates for the **Jinder Platform**.

## Documents in this Directory

| Document | Description |
|---|---|
| [**`PROMPT_ENGINEERING_PRINCIPLES.md`**](PROMPT_ENGINEERING_PRINCIPLES.md) | The 6 core prompt engineering principles, anti-hallucination rules, prompt injection defenses, and production system prompt templates. |
| [**`API_CONTRACT_PROMPT.md`**](API_CONTRACT_PROMPT.md) | The comprehensive API Contract and Prompt specification establishing the contract between frontend and backend. |

## Quick Summary of Prompt Guardrails
1. **Deterministic JSON Only:** Output must follow strict JSON schemas; no conversational chatter.
2. **Zero-PII Filter:** Demographics and contact data are strictly purged at the prompt boundary.
3. **Grounded Evidence:** Every detected skill requires verbatim quote evidence from source text.
4. **Adversarial Quarantine:** Untrusted candidate CV text is wrapped in `<untrusted_resume_content>` tags.
