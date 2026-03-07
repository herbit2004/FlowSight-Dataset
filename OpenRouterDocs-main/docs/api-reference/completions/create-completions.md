# Create a completion

POST https://openrouter.ai/api/v1/completions
Content-Type: application/json

Creates a completion for the provided prompt and parameters. Supports both streaming and non-streaming modes.

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create a completion
  version: endpoint_completions.createCompletions
paths:
  /completions:
    post:
      operationId: create-completions
      summary: Create a completion
      description: >-
        Creates a completion for the provided prompt and parameters. Supports
        both streaming and non-streaming modes.
      tags:
        - - subpackage_completions
      parameters:
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful completion response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompletionResponse'
        '400':
          description: Bad request - invalid parameters
          content: {}
        '401':
          description: Unauthorized - invalid API key
          content: {}
        '429':
          description: Too many requests - rate limit exceeded
          content: {}
        '500':
          description: Internal server error
          content: {}
      requestBody:
        description: Completion request parameters
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompletionCreateParams'
components:
  schemas:
    ModelName:
      type: string
    CompletionCreateParamsPrompt:
      oneOf:
        - type: string
        - type: array
          items:
            type: string
        - type: array
          items:
            type: number
            format: double
        - type: array
          items:
            type: array
            items:
              type: number
              format: double
    CompletionCreateParamsStop:
      oneOf:
        - type: string
        - type: array
          items:
            type: string
    CompletionCreateParamsStreamOptions:
      type: object
      properties:
        include_usage:
          type:
            - boolean
            - 'null'
    CompletionCreateParamsResponseFormat0:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
      required:
        - type
    CompletionCreateParamsResponseFormat1:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: json_object
      required:
        - type
    JSONSchemaConfig:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        schema:
          type: object
          additionalProperties:
            description: Any type
        strict:
          type:
            - boolean
            - 'null'
      required:
        - name
    ResponseFormatJSONSchema:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: json_schema
        json_schema:
          $ref: '#/components/schemas/JSONSchemaConfig'
      required:
        - type
        - json_schema
    ResponseFormatTextGrammar:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: grammar
        grammar:
          type: string
      required:
        - type
        - grammar
    CompletionCreateParamsResponseFormat4:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: python
      required:
        - type
    CompletionCreateParamsResponseFormat:
      oneOf:
        - $ref: '#/components/schemas/CompletionCreateParamsResponseFormat0'
        - $ref: '#/components/schemas/CompletionCreateParamsResponseFormat1'
        - $ref: '#/components/schemas/ResponseFormatJSONSchema'
        - $ref: '#/components/schemas/ResponseFormatTextGrammar'
        - $ref: '#/components/schemas/CompletionCreateParamsResponseFormat4'
    CompletionCreateParams:
      type: object
      properties:
        model:
          $ref: '#/components/schemas/ModelName'
        models:
          type: array
          items:
            $ref: '#/components/schemas/ModelName'
        prompt:
          $ref: '#/components/schemas/CompletionCreateParamsPrompt'
        best_of:
          type:
            - integer
            - 'null'
        echo:
          type:
            - boolean
            - 'null'
        frequency_penalty:
          type:
            - number
            - 'null'
          format: double
        logit_bias:
          type:
            - object
            - 'null'
          additionalProperties:
            type: number
            format: double
        logprobs:
          type:
            - integer
            - 'null'
        max_tokens:
          type:
            - integer
            - 'null'
        'n':
          type:
            - integer
            - 'null'
        presence_penalty:
          type:
            - number
            - 'null'
          format: double
        seed:
          type:
            - integer
            - 'null'
        stop:
          oneOf:
            - $ref: '#/components/schemas/CompletionCreateParamsStop'
            - type: 'null'
        stream:
          type: boolean
        stream_options:
          oneOf:
            - $ref: '#/components/schemas/CompletionCreateParamsStreamOptions'
            - type: 'null'
        suffix:
          type:
            - string
            - 'null'
        temperature:
          type:
            - number
            - 'null'
          format: double
        top_p:
          type:
            - number
            - 'null'
          format: double
        user:
          type: string
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            type: string
        response_format:
          oneOf:
            - $ref: '#/components/schemas/CompletionCreateParamsResponseFormat'
            - type: 'null'
      required:
        - prompt
    CompletionLogprobs:
      type: object
      properties:
        tokens:
          type: array
          items:
            type: string
        token_logprobs:
          type: array
          items:
            type: number
            format: double
        top_logprobs:
          type:
            - array
            - 'null'
          items:
            type: object
            additionalProperties:
              type: number
              format: double
        text_offset:
          type: array
          items:
            type: number
            format: double
      required:
        - tokens
        - token_logprobs
        - top_logprobs
        - text_offset
    CompletionFinishReason:
      type: string
      enum:
        - value: stop
        - value: length
        - value: content_filter
    CompletionChoice:
      type: object
      properties:
        text:
          type: string
        index:
          type: number
          format: double
        logprobs:
          oneOf:
            - $ref: '#/components/schemas/CompletionLogprobs'
            - type: 'null'
        finish_reason:
          $ref: '#/components/schemas/CompletionFinishReason'
      required:
        - text
        - index
        - logprobs
        - finish_reason
    CompletionUsage:
      type: object
      properties:
        prompt_tokens:
          type: number
          format: double
        completion_tokens:
          type: number
          format: double
        total_tokens:
          type: number
          format: double
      required:
        - prompt_tokens
        - completion_tokens
        - total_tokens
    CompletionResponse:
      type: object
      properties:
        id:
          type: string
        object:
          type: string
          enum:
            - type: stringLiteral
              value: text_completion
        created:
          type: number
          format: double
        model:
          type: string
        system_fingerprint:
          type: string
        choices:
          type: array
          items:
            $ref: '#/components/schemas/CompletionChoice'
        usage:
          $ref: '#/components/schemas/CompletionUsage'
      required:
        - id
        - object
        - created
        - model
        - choices

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/completions"

payload = { "prompt": "string" }
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/completions';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"prompt":"string"}'
};

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
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/completions"

	payload := strings.NewReader("{\n  \"prompt\": \"string\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

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

url = URI("https://openrouter.ai/api/v1/completions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"prompt\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/completions")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"prompt\": \"string\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/completions', [
  'body' => '{
  "prompt": "string"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/completions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"prompt\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = ["prompt": "string"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/completions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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