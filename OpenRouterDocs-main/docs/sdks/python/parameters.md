# Parameters - Python SDK

> Parameters method documentation for the OpenRouter Python SDK. Learn how to use this API endpoint with code examples.

(*parameters*)

## Overview

Parameters endpoints

### Available Operations

* [get\_parameters](#get_parameters) - Get a model's supported parameters and data about which are most popular

## get\_parameters

Get a model's supported parameters and data about which are most popular

### Example Usage

{/* UsageSnippet language="python" operationID="getParameters" method="get" path="/parameters/{author}/{slug}" */}

```python
from openrouter import OpenRouter, operations
import os

with OpenRouter() as open_router:

    res = open_router.parameters.get_parameters(security=operations.GetParametersSecurity(
        bearer=os.getenv("OPENROUTER_BEARER", ""),
    ), author="<value>", slug="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter  | Type                                                                                      | Required             | Description                                                         |
| ---------- | ----------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `security` | [operations.GetParametersSecurity](/docs/sdks/python/operations/getparameterssecurity)    | :heavy\_check\_mark: | N/A                                                                 |
| `author`   | *str*                                                                                     | :heavy\_check\_mark: | N/A                                                                 |
| `slug`     | *str*                                                                                     | :heavy\_check\_mark: | N/A                                                                 |
| `provider` | [Optional\[operations.GetParametersProvider\]](../../operations/getparametersprovider.md) | :heavy\_minus\_sign: | N/A                                                                 |
| `retries`  | [Optional\[utils.RetryConfig\]](../../models/utils/retryconfig.md)                        | :heavy\_minus\_sign: | Configuration to override the default retry behavior of the client. |

### Response

**[operations.GetParametersResponse](/docs/sdks/python/operations/getparametersresponse)**

### Errors

| Error Type                         | Status Code | Content Type     |
| ---------------------------------- | ----------- | ---------------- |
| errors.UnauthorizedResponseError   | 401         | application/json |
| errors.NotFoundResponseError       | 404         | application/json |
| errors.InternalServerResponseError | 500         | application/json |
| errors.OpenRouterDefaultError      | 4XX, 5XX    | \*/\*            |
