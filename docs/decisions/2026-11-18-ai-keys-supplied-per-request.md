# AI Keys Are Supplied Per Request

**Status:** Accepted
**Date:** 18 November, 2026
**Deciders:** Youpele Michael (owner), Claude Code

## Decision

The AI interpretation supports Anthropic, Azure OpenAI, Gemini, Groq, OpenAI and OpenRouter (DEMATELab's providers, model catalogue and services). Keys come with each `POST /explanations` request as a `SecretStr` (`repr=False`), are used once, and are never stored, logged or returned; validation errors log only field paths. Azure endpoints must be https on an Azure OpenAI host suffix and port 443 (SSRF guard). Timeouts are 120 s. The prompt and system message are the legacy ones (`llm_tab.py:79-196`) with temperature 0.3.

## Context

The legacy app sends the key from the desktop and clears it after each call (`llm_tab.py:841, 848`); a server must not become a key store.

## Alternatives Considered

- **Server-side keys in an env file:** the operator would pay for and expose every user's calls.

## Consequences

- Production must enable TLS in Nginx before the AI feature is used, because keys cross the network.
- Unlike `llm_tab.py:248`, OpenAI-compatible and Azure bodies send no `max_tokens` (newer OpenAI models reject it); Anthropic uses 4096.

## Related Work

- Plan: [Port The Policy Coherence Kit Backend To A Dockerised FastAPI `apps/api`](../plans/2026-11-18-port-backend-to-fastapi-api-plan.md)
- Conventions source: DEMATELab's decision records of 16 November, 2026 (`dematelab/docs/decisions/`)
