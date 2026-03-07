# APIKeys - Python SDK

> APIKeys method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*api\_keys*)

## Overview

API key management endpoints

### Available Operations

* [list](#list) - List API keys
* [create](#create) - Create a new API key
* [update](#update) - Update an API key
* [delete](#delete) - Delete an API key
* [get](#get) - Get a single API key
* [get\_current\_key\_metadata](#get_current_key_metadata) - Get current API key

## list

List API keys

### Example Usage

{/* UsageSnippet language="python" operationID="list" method="get" path="/keys" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.list(include_disabled="false", offset="0")

    # Handle response
    print(res)

```

### Parameters

| Parameter          | Type                                                               | Required             | Description                                                         | Example |
| ------------------ | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- | ------- |
| `include_disabled` | *Optional\[str]*                                                   | :heavy\_minus\_sign: | Whether to include disabled API keys in the response                | false   |
| `offset`           | *Optional\[str]*                                                   | :heavy\_minus\_sign: | Number of API keys to skip for pagination                           | 0       |
| `retries`          | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |         |

### Response

**[operations.ListResponse](/docs/sdks/python/operations/listresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |

## create

Create a new API key

### Example Usage

{/* UsageSnippet language="python" operationID="createKeys" method="post" path="/keys" */}

```python
from openrouter import OpenRouter
from openrouter.utils import parse_datetime
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.create(name="My New API Key", limit=50, limit_reset="monthly", include_byok_in_limit=True, expires_at=parse_datetime("2027-12-31T23:59:59Z"))

    # Handle response
    print(res)

```

### Parameters

| Parameter               | Type                                                                                            | Required             | Description                                                                                                                                                           | Example              |
| ----------------------- | ----------------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `name`                  | *str*                                                                                           | :heavy\_check\_mark: | Name for the new API key                                                                                                                                              | My New API Key       |
| `limit`                 | *OptionalNullable\[float]*                                                                      | :heavy\_minus\_sign: | Optional spending limit for the API key in USD                                                                                                                        | 50                   |
| `limit_reset`           | [OptionalNullable\[operations.CreateKeysLimitReset\]](../../operations/createkeyslimitreset.md) | :heavy\_minus\_sign: | Type of limit reset for the API key (daily, weekly, monthly, or null for no reset). Resets happen automatically at midnight UTC, and weeks are Monday through Sunday. | monthly              |
| `include_byok_in_limit` | *Optional\[bool]*                                                                               | :heavy\_minus\_sign: | Whether to include BYOK usage in the limit                                                                                                                            | true                 |
| `expires_at`            | [date](https://docs.python.org/3/library/datetime.html#date-objects)                            | :heavy\_minus\_sign: | Optional ISO 8601 UTC timestamp when the API key should expire. Must be UTC, other timezones will be rejected                                                         | 2027-12-31T23:59:59Z |
| `retries`               | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                              | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client.                                                                                                   |                      |

### Response

**[operations.CreateKeysResponse](/docs/sdks/python/operations/createkeysresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.BadRequestResponseError      | 400         | application/json |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |

## update

Update an API key

### Example Usage

{/* UsageSnippet language="python" operationID="updateKeys" method="patch" path="/keys/{hash}" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.update(hash="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", name="Updated API Key Name", disabled=False, limit=75, limit_reset="daily", include_byok_in_limit=True)

    # Handle response
    print(res)

```

### Parameters

| Parameter               | Type                                                                                            | Required             | Description                                                                                                                                                            | Example                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `hash`                  | *str*                                                                                           | :heavy\_check\_mark: | The hash identifier of the API key to update                                                                                                                           | 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 |
| `name`                  | *Optional\[str]*                                                                                | :heavy\_minus\_sign: | New name for the API key                                                                                                                                               | Updated API Key Name                                                      |
| `disabled`              | *Optional\[bool]*                                                                               | :heavy\_minus\_sign: | Whether to disable the API key                                                                                                                                         | false                                                                     |
| `limit`                 | *OptionalNullable\[float]*                                                                      | :heavy\_minus\_sign: | New spending limit for the API key in USD                                                                                                                              | 75                                                                        |
| `limit_reset`           | [OptionalNullable\[operations.UpdateKeysLimitReset\]](../../operations/updatekeyslimitreset.md) | :heavy\_minus\_sign: | New limit reset type for the API key (daily, weekly, monthly, or null for no reset). Resets happen automatically at midnight UTC, and weeks are Monday through Sunday. | daily                                                                     |
| `include_byok_in_limit` | *Optional\[bool]*                                                                               | :heavy\_minus\_sign: | Whether to include BYOK usage in the limit                                                                                                                             | true                                                                      |
| `retries`               | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                              | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client.                                                                                                    |                                                                           |

### Response

**[operations.UpdateKeysResponse](/docs/sdks/python/operations/updatekeysresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.BadRequestResponseError      | 400         | application/json |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.NotFoundResponseError        | 404         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |

## delete

Delete an API key

### Example Usage

{/* UsageSnippet language="python" operationID="deleteKeys" method="delete" path="/keys/{hash}" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.delete(hash="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")

    # Handle response
    print(res)

```

### Parameters

| Parameter | Type                                                               | Required             | Description                                                         | Example                                                                   |
| --------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `hash`    | *str*                                                              | :heavy\_check\_mark: | The hash identifier of the API key to delete                        | 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 |
| `retries` | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |                                                                           |

### Response

**[operations.DeleteKeysResponse](/docs/sdks/python/operations/deletekeysresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.NotFoundResponseError        | 404         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |

## get

Get a single API key

### Example Usage

{/* UsageSnippet language="python" operationID="getKey" method="get" path="/keys/{hash}" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.get(hash="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")

    # Handle response
    print(res)

```

### Parameters

| Parameter | Type                                                               | Required             | Description                                                         | Example                                                                   |
| --------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `hash`    | *str*                                                              | :heavy\_check\_mark: | The hash identifier of the API key to retrieve                      | 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 |
| `retries` | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |                                                                           |

### Response

**[operations.GetKeyResponse](/docs/sdks/python/operations/getkeyresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.NotFoundResponseError        | 404         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |

## get\_current\_key\_metadata

Get information on the API key associated with the current authentication session

### Example Usage

{/* UsageSnippet language="python" operationID="getCurrentKey" method="get" path="/key" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.api_keys.get_current_key_metadata()

    # Handle response
    print(res)

```

### Parameters

| Parameter | Type                                                               | Required             | Description                                                         |
| --------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- |
| `retries` | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.GetCurrentKeyResponse](/docs/sdks/python/operations/getcurrentkeyresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError   | 401         | application/json |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |
