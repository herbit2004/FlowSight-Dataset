# Get a single API key

GET https://openrouter.ai/api/v1/keys/{hash}

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get a single API key
  version: endpoint_apiKeys.getKey
paths:
  /keys/{hash}:
    get:
      operationId: get-key
      summary: Get a single API key
      tags:
        - - subpackage_apiKeys
      parameters:
        - name: hash
          in: path
          description: The hash identifier of the API key to retrieve
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: API key details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/API Keys_getKey_Response_200'
        '401':
          description: Unauthorized - Missing or invalid authentication
          content: {}
        '404':
          description: Not Found - API key does not exist
          content: {}
        '429':
          description: Too Many Requests - Rate limit exceeded
          content: {}
        '500':
          description: Internal Server Error
          content: {}
components:
  schemas:
    KeysHashGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        hash:
          type: string
        name:
          type: string
        label:
          type: string
        disabled:
          type: boolean
        limit:
          type:
            - number
            - 'null'
          format: double
        limit_remaining:
          type:
            - number
            - 'null'
          format: double
        limit_reset:
          type:
            - string
            - 'null'
        include_byok_in_limit:
          type: boolean
        usage:
          type: number
          format: double
        usage_daily:
          type: number
          format: double
        usage_weekly:
          type: number
          format: double
        usage_monthly:
          type: number
          format: double
        byok_usage:
          type: number
          format: double
        byok_usage_daily:
          type: number
          format: double
        byok_usage_weekly:
          type: number
          format: double
        byok_usage_monthly:
          type: number
          format: double
        created_at:
          type: string
        updated_at:
          type:
            - string
            - 'null'
        expires_at:
          type:
            - string
            - 'null'
          format: date-time
      required:
        - hash
        - name
        - label
        - disabled
        - limit
        - limit_remaining
        - limit_reset
        - include_byok_in_limit
        - usage
        - usage_daily
        - usage_weekly
        - usage_monthly
        - byok_usage
        - byok_usage_daily
        - byok_usage_weekly
        - byok_usage_monthly
        - created_at
        - updated_at
    API Keys_getKey_Response_200:
      type: object
      properties:
        data:
          $ref: >-
            #/components/schemas/KeysHashGetResponsesContentApplicationJsonSchemaData
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/keys/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"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/keys/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';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys/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"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys/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")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/keys/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")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/keys/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', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/keys/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");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys/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")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```