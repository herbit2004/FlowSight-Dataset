# Xcode

> Integrate OpenRouter with Apple Intelligence in Xcode 26. Complete setup guide for accessing hundreds of AI models directly in your Xcode development environment.

## Using Xcode with Apple Intelligence

[Apple Intelligence](https://developer.apple.com/apple-intelligence/) in Xcode 26 provides built-in AI assistance for coding. By integrating OpenRouter, you can access hundreds of AI models directly in your Xcode development environment, going far beyond the default ChatGPT integration.

This integration allows you to use models from Anthropic, Google, Meta, and many other providers without leaving your development environment.

### Prerequisites

<Callout intent="warn">
  Apple Intelligence on Xcode is currently in Beta and requires:

  * **macOS Tahoe 26.0 Beta** or later
  * **[Xcode 26 beta 4](https://developer.apple.com/download/applications/)** or later
</Callout>

### Setup Instructions

#### Step 1: Access Intelligence Settings

Navigate to **Settings > Intelligence > Add a Model Provider** in your macOS system preferences.

![Xcode Intelligence Settings](file:840a0f9a-8fe7-47fd-a7bc-5f086f923de3)

#### Step 2: Configure OpenRouter Provider

In the "Add a Model Provider" dialog, enter the following details:

* **URL**: `https://openrouter.ai/api`
  * **Important**: Do not add `/v1` at the end of the endpoint like you typically would for direct API calls
* **API Key Header**: `api_key`
* **API Key**: Your OpenRouter API key (starts with `sk-or-v1-`)
* **Description**: `OpenRouter` (or any name you prefer)

Click **Add** to save the configuration.

![OpenRouter Configuration](file:e5d60eea-e183-479b-ac91-facf1eed5eaf)

#### Step 3: Browse Available Models

Once configured, click on **OpenRouter** to see all available models. Since OpenRouter offers hundreds of models, you should bookmark your favorite models for quick access. Bookmarked models will appear at the top of the list, making them easily accessible from within the pane whenever you need them.

![Available Models](file:cd26b328-1567-4d0f-a12f-46aa0b41f525)

You'll have access to models from various providers including:

* Anthropic Claude models
* Google Gemini models
* Meta Llama models
* OpenAI GPT models
* And hundreds more

![Extended Model List](file:9d8669f7-6d46-4801-9a4d-987609a3b5f5)

#### Step 4: Start Using AI in Xcode

Head back to the chat interface (icon at the top) and start chatting with your selected models directly in Xcode.

![Xcode Chat Interface](file:18df1d71-52f9-4297-977a-1d1f17218433)

### Using Apple Intelligence Features

Once configured, you can use Apple Intelligence features in Xcode with OpenRouter models:

* **Code Completion**: Get intelligent code suggestions
* **Code Explanation**: Ask questions about your code
* **Refactoring Assistance**: Get help improving your code structure
* **Documentation Generation**: Generate comments and documentation

![Apple Intelligence Interface](file:835a0ce2-d8cc-4c11-9f27-5f52780efe26)

*Image credit: [Apple Developer Documentation](https://developer.apple.com/documentation/Xcode/writing-code-with-intelligence-in-xcode)*

### Learn More

* **Apple Intelligence Documentation**: [Writing Code with Intelligence in Xcode](https://developer.apple.com/documentation/Xcode/writing-code-with-intelligence-in-xcode)
* **OpenRouter Quick Start**: [Getting Started with OpenRouter](https://openrouter.ai/docs/quickstart)
* **Available Models**: [Browse OpenRouter Models](https://openrouter.ai/models)
