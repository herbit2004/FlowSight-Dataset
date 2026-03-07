# Responses - Python SDK

> Responses method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*beta.responses*)

## Overview

beta.responses endpoints

### Available Operations

* [send](#send) - Create a response

## send

Creates a streaming or non-streaming response using OpenResponses API format

### Example Usage

{/* UsageSnippet language="python" operationID="createResponses" method="post" path="/responses" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.beta.responses.send(input=[
        {
            "type": "message",
            "role": "user",
            "content": "Hello, how are you?",
        },
    ], metadata={
        "user_id": "123",
        "session_id": "abc-def-ghi",
    }, tools=[
        {
            "type": "function",
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                    },
                },
            },
        },
    ], model="anthropic/claude-4.5-sonnet-20250929", text={
        "format_": {
            "type": "text",
        },
        "verbosity": "medium",
    }, reasoning={
        "summary": "auto",
        "enabled": True,
    }, temperature=0.7, top_p=0.9, prompt={
        "id": "<id>",
        "variables": {
            "key": {
                "type": "input_text",
                "text": "Hello, how can I help you?",
            },
        },
    }, service_tier="auto", truncation="auto", stream=False, provider={
        "data_collection": "allow",
        "zdr": True,
        "enforce_distillable_text": True,
        "order": [
            "OpenAI",
        ],
        "only": [
            "OpenAI",
        ],
        "ignore": [
            "OpenAI",
        ],
        "quantizations": None,
        "sort": "price",
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter              | Type                                                                                                            | Required             | Description                                                                                                                                                                                                                                                                                          | Example                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `input`                | [Optional\[components.OpenResponsesInput\]](../../components/openresponsesinput.md)                             | :heavy\_minus\_sign: | Input for a response request - can be a string or array of items                                                                                                                                                                                                                                     | \[<br />`{"role": "user","content": "What is the weather today?"}`<br />] |
| `instructions`         | *OptionalNullable\[str]*                                                                                        | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `metadata`             | Dict\[str, *str*]                                                                                               | :heavy\_minus\_sign: | Metadata key-value pairs for the request. Keys must be â¤64 characters and cannot contain brackets. Values must be â¤512 characters. Maximum 16 pairs allowed.                                                                                                                                         | `{"user_id": "123","session_id": "abc-def-ghi"}`                          |
| `tools`                | List\[[components.OpenResponsesRequestToolUnion](/docs/sdks/python/components/openresponsesrequesttoolunion)]   | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `tool_choice`          | [Optional\[components.OpenAIResponsesToolChoiceUnion\]](../../components/openairesponsestoolchoiceunion.md)     | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `parallel_tool_calls`  | *OptionalNullable\[bool]*                                                                                       | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `model`                | *Optional\[str]*                                                                                                | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `models`               | List\[*str*]                                                                                                    | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `text`                 | [Optional\[components.OpenResponsesResponseText\]](../../components/openresponsesresponsetext.md)               | :heavy\_minus\_sign: | Text output configuration including format and verbosity                                                                                                                                                                                                                                             | `{"format": {"type": "text"}`,<br />"verbosity": "medium"<br />}          |
| `reasoning`            | [OptionalNullable\[components.OpenResponsesReasoningConfig\]](../../components/openresponsesreasoningconfig.md) | :heavy\_minus\_sign: | Configuration for reasoning mode in the response                                                                                                                                                                                                                                                     | `{"summary": "auto","enabled": true}`                                     |
| `max_output_tokens`    | *OptionalNullable\[float]*                                                                                      | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `temperature`          | *OptionalNullable\[float]*                                                                                      | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `top_p`                | *OptionalNullable\[float]*                                                                                      | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `top_k`                | *Optional\[float]*                                                                                              | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `prompt_cache_key`     | *OptionalNullable\[str]*                                                                                        | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `previous_response_id` | *OptionalNullable\[str]*                                                                                        | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `prompt`               | [OptionalNullable\[components.OpenAIResponsesPrompt\]](../../components/openairesponsesprompt.md)               | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `include`              | List\[[components.OpenAIResponsesIncludable](/docs/sdks/python/components/openairesponsesincludable)]           | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `background`           | *OptionalNullable\[bool]*                                                                                       | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `safety_identifier`    | *OptionalNullable\[str]*                                                                                        | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `store`                | *OptionalNullable\[bool]*                                                                                       | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `service_tier`         | [OptionalNullable\[components.ServiceTier\]](../../components/servicetier.md)                                   | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  | auto                                                                      |
| `truncation`           | [OptionalNullable\[components.Truncation\]](../../components/truncation.md)                                     | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  | auto                                                                      |
| `stream`               | *Optional\[bool]*                                                                                               | :heavy\_minus\_sign: | N/A                                                                                                                                                                                                                                                                                                  |                                                                           |
| `provider`             | [OptionalNullable\[components.Provider\]](../../components/provider.md)                                         | :heavy\_minus\_sign: | When multiple model providers are available, optionally indicate your routing preference.                                                                                                                                                                                                            |                                                                           |
| `plugins`              | List\[[components.Plugin](/docs/sdks/python/components/plugin)]                                                 | :heavy\_minus\_sign: | Plugins you want to enable for this request, including their settings.                                                                                                                                                                                                                               |                                                                           |
| `user`                 | *Optional\[str]*                                                                                                | :heavy\_minus\_sign: | A unique identifier representing your end-user, which helps distinguish between different users of your app. This allows your app to identify specific users in case of abuse reports, preventing your entire app from being affected by the actions of individual users. Maximum of 128 characters. |                                                                           |
| `retries`              | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                                              | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                  |                                                                           |

### Response

**[operations.CreateResponsesResponse](/docs/sdks/python/operations/createresponsesresponse)**

### Errors

| Error Type                              | Status Code | Content Type     |
| --------------------------------------- | ----------- | ---------------- |
| errors.BadRequestResponseError          | 400         | application/json |
| errors.UnauthorizedResponseError        | 401         | application/json |
| errors.PaymentRequiredResponseError     | 402         | application/json |
| errors.NotFoundResponseError            | 404         | application/json |
| errors.RequestTimeoutResponseError      | 408         | application/json |
| errors.PayloadTooLargeResponseError     | 413         | application/json |
| errors.UnprocessableEntityResponseError | 422         | application/json |
| errors.TooManyRequestsResponseError     | 429         | application/json |
| errors.InternalServerResponseError      | 500         | application/json |
| errors.BadGatewayResponseError          | 502         | application/json |
| errors.ServiceUnavailableResponseError  | 503         | application/json |
| errors.EdgeNetworkTimeoutResponseError  | 524         | application/json |
| errors.ProviderOverloadedResponseError  | 529         | application/json |
| errors.OpenRouterDefaultError           | 4XX, 5XX    | \*/\*            |
