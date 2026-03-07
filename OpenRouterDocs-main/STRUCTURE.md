# OpenRouter Documentation Repository Structure

This repository contains a complete mirror of the OpenRouter.ai documentation in Markdown format.

## Repository Organization

```
OpenRouterDocs/
├── README.md                    # Main navigation and introduction
├── STRUCTURE.md                 # This file - repository structure documentation
└── docs/                        # All documentation files
    ├── index.md                 # Documentation home page
    ├── quickstart.md            # Quick start guide
    ├── faq.md                   # Frequently asked questions
    ├── app-attribution.md       # App attribution guide
    │
    ├── overview/                # Overview section (2 files)
    │   ├── models.md
    │   └── principles.md
    │
    ├── features/                # Features section (21 files)
    │   ├── exacto-variant.md
    │   ├── latency-and-performance.md
    │   ├── message-transforms.md
    │   ├── model-routing.md
    │   ├── presets.md
    │   ├── privacy-and-logging.md
    │   ├── prompt-caching.md
    │   ├── provider-routing.md
    │   ├── provisioning-api-keys.md
    │   ├── structured-outputs.md
    │   ├── tool-calling.md
    │   ├── uptime-optimization.md
    │   ├── web-search.md
    │   ├── zdr.md
    │   ├── zero-completion-insurance.md
    │   └── multimodal/          # Multimodal subsection (6 files)
    │       ├── overview.md
    │       ├── images.md
    │       ├── audio.md
    │       ├── videos.md
    │       ├── pdfs.md
    │       └── image-generation.md
    │
    ├── api-reference/           # API Reference section (44 files)
    │   ├── overview.md
    │   ├── authentication.md
    │   ├── streaming.md
    │   ├── embeddings.md
    │   ├── limits.md
    │   ├── parameters.md
    │   ├── errors.md
    │   ├── analytics/
    │   │   └── get-user-activity.md
    │   ├── api-keys/
    │   │   ├── list.md
    │   │   ├── create-keys.md
    │   │   ├── get-key.md
    │   │   ├── get-current-key.md
    │   │   ├── update-keys.md
    │   │   └── delete-keys.md
    │   ├── beta-responses/
    │   │   └── create-responses.md
    │   ├── chat/
    │   │   └── send-chat-completion-request.md
    │   ├── completions/
    │   │   └── create-completions.md
    │   ├── credits/
    │   │   ├── get-credits.md
    │   │   └── create-coinbase-charge.md
    │   ├── embeddings/
    │   │   ├── create-embeddings.md
    │   │   └── list-embeddings-models.md
    │   ├── endpoints/
    │   │   ├── list-endpoints.md
    │   │   └── list-endpoints-zdr.md
    │   ├── generations/
    │   │   └── get-generation.md
    │   ├── models/
    │   │   ├── get-models.md
    │   │   ├── list-models-count.md
    │   │   └── list-models-user.md
    │   ├── o-auth/
    │   │   ├── create-auth-keys-code.md
    │   │   └── exchange-auth-code-for-api-key.md
    │   ├── parameters/
    │   │   └── get-parameters.md
    │   ├── providers/
    │   │   └── list-providers.md
    │   └── responses-api/
    │       ├── overview.md
    │       ├── basic-usage.md
    │       ├── reasoning.md
    │       ├── tool-calling.md
    │       ├── web-search.md
    │       └── error-handling.md
    │
    ├── community/               # Community integrations (10 files)
    │   ├── frameworks-and-integrations-overview.md
    │   ├── effect-ai-sdk.md
    │   ├── arize.md
    │   ├── lang-chain.md
    │   ├── langfuse.md
    │   ├── live-kit.md
    │   ├── mastra.md
    │   ├── open-ai-sdk.md
    │   ├── pydantic-ai.md
    │   ├── vercel-ai-sdk.md
    │   ├── xcode.md
    │   └── zapier.md
    │
    ├── use-cases/               # Use cases (9 files)
    │   ├── byok.md
    │   ├── crypto-api.md
    │   ├── for-providers.md
    │   ├── mcp-servers.md
    │   ├── oauth-pkce.md
    │   ├── organization-management.md
    │   ├── reasoning-tokens.md
    │   ├── usage-accounting.md
    │   └── user-tracking.md
    │
    └── sdks/                    # SDK Documentation (26 files)
        ├── python/              # Python SDK (13 files)
        │   ├── analytics.md
        │   ├── apikeys.md
        │   ├── chat.md
        │   ├── completions.md
        │   ├── credits.md
        │   ├── embeddings.md
        │   ├── endpoints.md
        │   ├── generations.md
        │   ├── models.md
        │   ├── oauth.md
        │   ├── parameters.md
        │   ├── providers.md
        │   └── responses.md
        └── typescript/          # TypeScript SDK (13 files)
            ├── analytics.md
            ├── apikeys.md
            ├── chat.md
            ├── completions.md
            ├── credits.md
            ├── embeddings.md
            ├── endpoints.md
            ├── generations.md
            ├── models.md
            ├── oauth.md
            ├── parameters.md
            ├── providers.md
            └── responses.md
```

## Statistics

- **Total Documentation Files**: 111
- **Main Sections**: 7
  - Overview: 2 files
  - Features: 21 files (including 6 multimodal subsection files)
  - API Reference: 44 files (including subsections)
  - Community: 10 files
  - Use Cases: 9 files
  - SDKs: 26 files (13 Python + 13 TypeScript)
  - Root Level: 4 files

## Documentation Coverage

### ✅ Successfully Retrieved (111 pages)

All 111 documentation pages were successfully retrieved from the official OpenRouter.ai website.

### 📋 Content Sources

- **Primary Method**: Direct `.md` endpoint access (preferred)
- **Fallback Method**: HTML parsing and conversion to Markdown

## Update Information

- **Last Updated**: November 16, 2025
- **Source**: https://openrouter.ai/docs/
- **Branch**: AllLinks
- **Extraction Method**: Automated parsing with full navigation expansion
- **Success Rate**: 100% (111/111 pages)

## Notes

- All files are in Markdown format for easy reading and integration
- File structure mirrors the official documentation hierarchy
- Subdirectories are used to maintain logical grouping
- All links and references are preserved from the original documentation
- This version includes significantly more content than the initial main branch (111 vs 42 files)
