# Get user activity grouped by endpoint

GET https://openrouter.ai/api/v1/activity

Returns user activity data grouped by endpoint for the last 30 (completed) UTC days

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get user activity grouped by endpoint
  version: endpoint_analytics.getUserActivity
paths:
  /activity:
    get:
      operationId: get-user-activity
      summary: Get user activity grouped by endpoint
      description: >-
        Returns user activity data grouped by endpoint for the last 30
        (completed) UTC days
      tags:
        - - subpackage_analytics
      parameters:
        - name: date
          in: query
          description: Filter by a single UTC date in the last 30 days (YYYY-MM-DD format).
          required: false
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
          description: Returns user activity data grouped by endpoint
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Analytics_getUserActivity_Response_200'
        '400':
          description: Bad Request - Invalid date format or date range
          content: {}
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '403':
          description: Forbidden - Only provisioning keys can fetch activity
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
components:
  schemas:
    ActivityItem:
      type: object
      properties:
        date:
          type: string
        model:
          type: string
        model_permaslug:
          type: string
        endpoint_id:
          type: string
        provider_name:
          type: string
        usage:
          type: number
          format: double
        byok_usage_inference:
          type: number
          format: double
        requests:
          type: number
          format: double
        prompt_tokens:
          type: number
          format: double
        completion_tokens:
          type: number
          format: double
        reasoning_tokens:
          type: number
          format: double
      required:
        - date
        - model
        - model_permaslug
        - endpoint_id
        - provider_name
        - usage
        - byok_usage_inference
        - requests
        - prompt_tokens
        - completion_tokens
        - reasoning_tokens
    Analytics_getUserActivity_Response_200:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/ActivityItem'
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/activity"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/activity';
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

	url := "https://openrouter.ai/api/v1/activity"

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

url = URI("https://openrouter.ai/api/v1/activity")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/activity")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/activity', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/activity");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/activity")! as URL,
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