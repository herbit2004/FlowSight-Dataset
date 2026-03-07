# Completions - Python SDK

> Completions method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*completions*)

## Overview

### Available Operations

* [generate](#generate) - Create a completion

## generate

Creates a completion for the provided prompt and parameters. Supports both streaming and non-streaming modes.

### Example Usage

{/* UsageSnippet language="python" operationID="createCompletions" method="post" path="/completions" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.completions.generate(prompt=[], stream=False)

    # Handle response
    print(res)

```

### Parameters

| Parameter           | Type                                                                                                                                      | Required             | Description                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `prompt`            | [components.Prompt](/docs/sdks/python/components/prompt)                                                                                  | :heavy\_check\_mark: | N/A                                                                 |
| `model`             | *Optional\[str]*                                                                                                                          | :heavy\_minus\_sign: | N/A                                                                 |
| `models`            | List\[*str*]                                                                                                                              | :heavy\_minus\_sign: | N/A                                                                 |
| `best_of`           | *OptionalNullable\[int]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `echo`              | *OptionalNullable\[bool]*                                                                                                                 | :heavy\_minus\_sign: | N/A                                                                 |
| `frequency_penalty` | *OptionalNullable\[float]*                                                                                                                | :heavy\_minus\_sign: | N/A                                                                 |
| `logit_bias`        | Dict\[str, *float*]                                                                                                                       | :heavy\_minus\_sign: | N/A                                                                 |
| `logprobs`          | *OptionalNullable\[int]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `max_tokens`        | *OptionalNullable\[int]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `n`                 | *OptionalNullable\[int]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `presence_penalty`  | *OptionalNullable\[float]*                                                                                                                | :heavy\_minus\_sign: | N/A                                                                 |
| `seed`              | *OptionalNullable\[int]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `stop`              | [OptionalNullable\[components.CompletionCreateParamsStop\]](../../components/completioncreateparamsstop.md)                               | :heavy\_minus\_sign: | N/A                                                                 |
| `stream`            | *Optional\[bool]*                                                                                                                         | :heavy\_minus\_sign: | N/A                                                                 |
| `stream_options`    | [OptionalNullable\[components.StreamOptions\]](../../components/streamoptions.md)                                                         | :heavy\_minus\_sign: | N/A                                                                 |
| `suffix`            | *OptionalNullable\[str]*                                                                                                                  | :heavy\_minus\_sign: | N/A                                                                 |
| `temperature`       | *OptionalNullable\[float]*                                                                                                                | :heavy\_minus\_sign: | N/A                                                                 |
| `top_p`             | *OptionalNullable\[float]*                                                                                                                | :heavy\_minus\_sign: | N/A                                                                 |
| `user`              | *Optional\[str]*                                                                                                                          | :heavy\_minus\_sign: | N/A                                                                 |
| `metadata`          | Dict\[str, *str*]                                                                                                                         | :heavy\_minus\_sign: | N/A                                                                 |
| `response_format`   | [OptionalNullable\[components.CompletionCreateParamsResponseFormatUnion\]](../../components/completioncreateparamsresponseformatunion.md) | :heavy\_minus\_sign: | N/A                                                                 |
| `retries`           | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                                                                        | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[components.CompletionResponse](/docs/sdks/python/components/completionresponse)**

### Errors

| Error Type                    | Status Code   | Content Type     |
| ----------------------------- | ------------- | ---------------- |
| errors.ChatError              | 400, 401, 429 | application/json |
| errors.ChatError              | 500           | application/json |
| errors.OpenRouterDefaultError | 4XX, 5XX      | \*/\*            |
