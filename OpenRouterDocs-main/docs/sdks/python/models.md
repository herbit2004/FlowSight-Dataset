# Models - Python SDK

> Models method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*models*)

## Overview

Model information endpoints

### Available Operations

* [count](#count) - Get total count of available models
* [list](#list) - List all models and their properties
* [list\_for\_user](#list_for_user) - List models filtered by user provider preferences

## count

Get total count of available models

### Example Usage

{/* UsageSnippet language="python" operationID="listModelsCount" method="get" path="/models/count" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.models.count()

    # Handle response
    print(res)

```

### Parameters

| Parameter | Type                                                               | Required             | Description                                                         |
| --------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- |
| `retries` | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[components.ModelsCountResponse](/docs/sdks/python/components/modelscountresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |

## list

List all models and their properties

### Example Usage

{/* UsageSnippet language="python" operationID="getModels" method="get" path="/models" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.models.list()

    # Handle response
    print(res)

```

### Parameters

| Parameter              | Type                                                               | Required             | Description                                                         |
| ---------------------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- |
| `category`             | *Optional\[str]*                                                   | :heavy\_minus\_sign: | N/A                                                                 |
| `supported_parameters` | *Optional\[str]*                                                   | :heavy\_minus\_sign: | N/A                                                                 |
| `use_rss`              | *Optional\[str]*                                                   | :heavy\_minus\_sign: | N/A                                                                 |
| `use_rss_chat_links`   | *Optional\[str]*                                                   | :heavy\_minus\_sign: | N/A                                                                 |
| `retries`              | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.GetModelsResponse](/docs/sdks/python/operations/getmodelsresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.BadRequestResponseError     | 400         | application/json |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |

## list\_for\_user

List models filtered by user provider preferences

### Example Usage

{/* UsageSnippet language="python" operationID="listModelsUser" method="get" path="/models/user" */}

```python
from openrouter import OpenRouter, operations
import os

with OpenRouter() as open_router:

    res = open_router.models.list_for_user(security=operations.ListModelsUserSecurity(
        bearer=os.getenv("OPENROUTER_BEARER", ""),
    ))

    # Handle response
    print(res)

```

### Parameters

| Parameter  | Type                                                                                     | Required             | Description                                                         |
| ---------- | ---------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `security` | [operations.ListModelsUserSecurity](/docs/sdks/python/operations/listmodelsusersecurity) | :heavy\_check\_mark: | The security requirements to use for the request.                   |
| `retries`  | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                       | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[components.ModelsListResponse](/docs/sdks/python/components/modelslistresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError   | 401         | application/json |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |
