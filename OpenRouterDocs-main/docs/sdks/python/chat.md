# Chat - Python SDK

> Chat method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*chat*)

## Overview

### Available Operations

* [send](#send) - Create a chat completion

## send

Sends a request for a model response for the given chat conversation. Supports both streaming and non-streaming modes.

### Example Usage

{/* UsageSnippet language="python" operationID="sendChatCompletionRequest" method="post" path="/chat/completions" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.chat.send(messages=[], stream=False)

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter               | Type                                                                                                                          | Required             | Description                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `messages`              | List\[[components.Message](/docs/sdks/python/components/message)]                                                             | :heavy\_check\_mark: | N/A                                                                 |
| `model`                 | *Optional\[str]*                                                                                                              | :heavy\_minus\_sign: | N/A                                                                 |
| `models`                | List\[*str*]                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `frequency_penalty`     | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `logit_bias`            | Dict\[str, *float*]                                                                                                           | :heavy\_minus\_sign: | N/A                                                                 |
| `logprobs`              | *OptionalNullable\[bool]*                                                                                                     | :heavy\_minus\_sign: | N/A                                                                 |
| `top_logprobs`          | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `max_completion_tokens` | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `max_tokens`            | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `metadata`              | Dict\[str, *str*]                                                                                                             | :heavy\_minus\_sign: | N/A                                                                 |
| `presence_penalty`      | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `reasoning`             | [Optional\[components.Reasoning\]](../../components/reasoning.md)                                                             | :heavy\_minus\_sign: | N/A                                                                 |
| `response_format`       | [Optional\[components.ChatGenerationParamsResponseFormatUnion\]](../../components/chatgenerationparamsresponseformatunion.md) | :heavy\_minus\_sign: | N/A                                                                 |
| `seed`                  | *OptionalNullable\[int]*                                                                                                      | :heavy\_minus\_sign: | N/A                                                                 |
| `stop`                  | [OptionalNullable\[components.ChatGenerationParamsStop\]](../../components/chatgenerationparamsstop.md)                       | :heavy\_minus\_sign: | N/A                                                                 |
| `stream`                | *Optional\[bool]*                                                                                                             | :heavy\_minus\_sign: | N/A                                                                 |
| `stream_options`        | [OptionalNullable\[components.ChatStreamOptions\]](../../components/chatstreamoptions.md)                                     | :heavy\_minus\_sign: | N/A                                                                 |
| `temperature`           | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `tool_choice`           | *Optional\[Any]*                                                                                                              | :heavy\_minus\_sign: | N/A                                                                 |
| `tools`                 | List\[[components.ToolDefinitionJSON](/docs/sdks/python/components/tooldefinitionjson)]                                       | :heavy\_minus\_sign: | N/A                                                                 |
| `top_p`                 | *OptionalNullable\[float]*                                                                                                    | :heavy\_minus\_sign: | N/A                                                                 |
| `user`                  | *Optional\[str]*                                                                                                              | :heavy\_minus\_sign: | N/A                                                                 |
| `retries`               | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                                                            | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.SendChatCompletionRequestResponse](/docs/sdks/python/operations/sendchatcompletionrequestresponse)**

### Errors

| Error Type                    | Status Code   | Content Type     |
| ----------------------------- | ------------- | ---------------- |
| errors.ChatError              | 400, 401, 429 | application/json |
| errors.ChatError              | 500           | application/json |
| errors.OpenRouterDefaultError | 4XX, 5XX      | \*/\*            |
