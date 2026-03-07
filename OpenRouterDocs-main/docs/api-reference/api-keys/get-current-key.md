# Get current API key

GET https://openrouter.ai/api/v1/key

Get information on the API key associated with the current authentication session

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get current API key
  version: endpoint_apiKeys.getCurrentKey
paths:
  /key:
    get:
      operationId: get-current-key
      summary: Get current API key
      description: >-
        Get information on the API key associated with the current
        authentication session
      tags:
        - - subpackage_apiKeys
      parameters:
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
                $ref: '#/components/schemas/API Keys_getCurrentKey_Response_200'
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
components:
  schemas:
    KeyGetResponsesContentApplicationJsonSchemaDataRateLimit:
      type: object
      properties:
        requests:
          type: number
          format: double
        interval:
          type: string
        note:
          type: string
      required:
        - requests
        - interval
        - note
    KeyGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        label:
          type: string
        limit:
          type:
            - number
            - 'null'
          format: double
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
        is_free_tier:
          type: boolean
        is_provisioning_key:
          type: boolean
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
        expires_at:
          type:
            - string
            - 'null'
          format: date-time
        rate_limit:
          $ref: >-
            #/components/schemas/KeyGetResponsesContentApplicationJsonSchemaDataRateLimit
      required:
        - label
        - limit
        - usage
        - usage_daily
        - usage_weekly
        - usage_monthly
        - byok_usage
        - byok_usage_daily
        - byok_usage_weekly
        - byok_usage_monthly
        - is_free_tier
        - is_provisioning_key
        - limit_remaining
        - limit_reset
        - include_byok_in_limit
        - rate_limit
    API Keys_getCurrentKey_Response_200:
      type: object
      properties:
        data:
          $ref: '#/components/schemas/KeyGetResponsesContentApplicationJsonSchemaData'
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/key"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/key';
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

	url := "https://openrouter.ai/api/v1/key"

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

url = URI("https://openrouter.ai/api/v1/key")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/key")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/key', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/key");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/key")! as URL,
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