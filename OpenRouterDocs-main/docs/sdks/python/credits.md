# Credits - Python SDK

> Credits method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*credits*)

## Overview

Credit management endpoints

### Available Operations

* [get\_credits](#get_credits) - Get remaining credits
* [create\_coinbase\_charge](#create_coinbase_charge) - Create a Coinbase charge for crypto payment

## get\_credits

Get total credits purchased and used for the authenticated user

### Example Usage

{/* UsageSnippet language="python" operationID="getCredits" method="get" path="/credits" */}

```python
from openrouter import OpenRouter
import os

with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
) as open_router:

    res = open_router.credits.get_credits()

    # Handle response
    print(res)

```

### Parameters

| Parameter | Type                                                               | Required             | Description                                                         |
| --------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------- |
| `retries` | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md) | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.GetCreditsResponse](/docs/sdks/python/operations/getcreditsresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError   | 401         | application/json |
| errors.ForbiddenResponseError      | 403         | application/json |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |

## create\_coinbase\_charge

Create a Coinbase charge for crypto payment

### Example Usage

{/* UsageSnippet language="python" operationID="createCoinbaseCharge" method="post" path="/credits/coinbase" */}

```python
from openrouter import OpenRouter, operations
import os

with OpenRouter() as open_router:

    res = open_router.credits.create_coinbase_charge(security=operations.CreateCoinbaseChargeSecurity(
        bearer=os.getenv("OPENROUTER_BEARER", ""),
    ), amount=100, sender="0x1234567890123456789012345678901234567890", chain_id=1)

    # Handle response
    print(res)

```

### Parameters

| Parameter  | Type                                                                                                 | Required             | Description                                                         |
| ---------- | ---------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `security` | [operations.CreateCoinbaseChargeSecurity](/docs/sdks/python/operations/createcoinbasechargesecurity) | :heavy\_check\_mark: | N/A                                                                 |
| `amount`   | *float*                                                                                              | :heavy\_check\_mark: | N/A                                                                 |
| `sender`   | *str*                                                                                                | :heavy\_check\_mark: | N/A                                                                 |
| `chain_id` | [components.ChainID](/docs/sdks/python/components/chainid)                                           | :heavy\_check\_mark: | N/A                                                                 |
| `retries`  | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                                   | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.CreateCoinbaseChargeResponse](/docs/sdks/python/operations/createcoinbasechargeresponse)**

### Errors

| Error Type                          | Status Code | Content Type     |
| ----------------------------------- | ----------- | ---------------- |
| errors.BadRequestResponseError      | 400         | application/json |
| errors.UnauthorizedResponseError    | 401         | application/json |
| errors.TooManyRequestsResponseError | 429         | application/json |
| errors.InternalServerResponseError  | 500         | application/json |
| errors.OpenRouterDefaultError       | 4XX, 5XX    | \*/\*            |
