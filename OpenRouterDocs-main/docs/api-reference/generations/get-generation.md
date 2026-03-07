# Get request & usage metadata for a generation

GET https://openrouter.ai/api/v1/generation

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get request & usage metadata for a generation
  version: endpoint_generations.getGeneration
paths:
  /generation:
    get:
      operationId: get-generation
      summary: Get request & usage metadata for a generation
      tags:
        - - subpackage_generations
      parameters:
        - name: id
          in: query
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
          description: Returns the request metadata for this generation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Generations_getGeneration_Response_200'
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '402':
          description: Payment Required - Insufficient credits or quota to complete request
          content: {}
        '404':
          description: Not Found - Generation not found
          content: {}
        '429':
          description: Too Many Requests - Rate limit exceeded
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
        '502':
          description: Bad Gateway - Provider/upstream API failure
          content: {}
components:
  schemas:
    GenerationGetResponsesContentApplicationJsonSchemaDataApiType:
      type: string
      enum:
        - value: completions
        - value: embeddings
    GenerationGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        id:
          type: string
        upstream_id:
          type:
            - string
            - 'null'
        total_cost:
          type: number
          format: double
        cache_discount:
          type:
            - number
            - 'null'
          format: double
        upstream_inference_cost:
          type:
            - number
            - 'null'
          format: double
        created_at:
          type: string
        model:
          type: string
        app_id:
          type:
            - number
            - 'null'
          format: double
        streamed:
          type:
            - boolean
            - 'null'
        cancelled:
          type:
            - boolean
            - 'null'
        provider_name:
          type:
            - string
            - 'null'
        latency:
          type:
            - number
            - 'null'
          format: double
        moderation_latency:
          type:
            - number
            - 'null'
          format: double
        generation_time:
          type:
            - number
            - 'null'
          format: double
        finish_reason:
          type:
            - string
            - 'null'
        tokens_prompt:
          type:
            - number
            - 'null'
          format: double
        tokens_completion:
          type:
            - number
            - 'null'
          format: double
        native_tokens_prompt:
          type:
            - number
            - 'null'
          format: double
        native_tokens_completion:
          type:
            - number
            - 'null'
          format: double
        native_tokens_completion_images:
          type:
            - number
            - 'null'
          format: double
        native_tokens_reasoning:
          type:
            - number
            - 'null'
          format: double
        native_tokens_cached:
          type:
            - number
            - 'null'
          format: double
        num_media_prompt:
          type:
            - number
            - 'null'
          format: double
        num_input_audio_prompt:
          type:
            - number
            - 'null'
          format: double
        num_media_completion:
          type:
            - number
            - 'null'
          format: double
        num_search_results:
          type:
            - number
            - 'null'
          format: double
        origin:
          type: string
        usage:
          type: number
          format: double
        is_byok:
          type: boolean
        native_finish_reason:
          type:
            - string
            - 'null'
        external_user:
          type:
            - string
            - 'null'
        api_type:
          oneOf:
            - $ref: >-
                #/components/schemas/GenerationGetResponsesContentApplicationJsonSchemaDataApiType
            - type: 'null'
      required:
        - id
        - upstream_id
        - total_cost
        - cache_discount
        - upstream_inference_cost
        - created_at
        - model
        - app_id
        - streamed
        - cancelled
        - provider_name
        - latency
        - moderation_latency
        - generation_time
        - finish_reason
        - tokens_prompt
        - tokens_completion
        - native_tokens_prompt
        - native_tokens_completion
        - native_tokens_completion_images
        - native_tokens_reasoning
        - native_tokens_cached
        - num_media_prompt
        - num_input_audio_prompt
        - num_media_completion
        - num_search_results
        - origin
        - usage
        - is_byok
        - native_finish_reason
        - external_user
        - api_type
    Generations_getGeneration_Response_200:
      type: object
      properties:
        data:
          $ref: >-
            #/components/schemas/GenerationGetResponsesContentApplicationJsonSchemaData
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/generation"

querystring = {"id":"id"}

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/generation?id=id';
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

	url := "https://openrouter.ai/api/v1/generation?id=id"

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

url = URI("https://openrouter.ai/api/v1/generation?id=id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/generation?id=id")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/generation?id=id', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/generation?id=id");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/generation?id=id")! as URL,
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