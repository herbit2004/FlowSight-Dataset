# Submit an embedding request

POST https://openrouter.ai/api/v1/embeddings
Content-Type: application/json

Submits an embedding request to the embeddings router

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Submit an embedding request
  version: endpoint_embeddings.createEmbeddings
paths:
  /embeddings:
    post:
      operationId: create-embeddings
      summary: Submit an embedding request
      description: Submits an embedding request to the embeddings router
      tags:
        - - subpackage_embeddings
      parameters:
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Embedding response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Embeddings_createEmbeddings_Response_200'
        '400':
          description: Bad Request - Invalid request parameters or malformed input
          content: {}
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '402':
          description: Payment Required - Insufficient credits or quota to complete request
          content: {}
        '404':
          description: Not Found - Resource does not exist
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
        '503':
          description: Service Unavailable - Service temporarily unavailable
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                input:
                  $ref: >-
                    #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInput
                model:
                  type: string
                encoding_format:
                  $ref: >-
                    #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaEncodingFormat
                user:
                  type: string
                provider:
                  $ref: >-
                    #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaProvider
                input_type:
                  type: string
              required:
                - input
                - model
components:
  schemas:
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf0Type:
      type: string
      enum:
        - value: text
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems0:
      type: object
      properties:
        type:
          $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf0Type
        text:
          type: string
      required:
        - type
        - text
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf1Type:
      type: string
      enum:
        - value: image_url
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf1ImageUrl:
      type: object
      properties:
        url:
          type: string
      required:
        - url
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems1:
      type: object
      properties:
        type:
          $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf1Type
        image_url:
          $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItemsOneOf1ImageUrl
      required:
        - type
        - image_url
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems:
      oneOf:
        - $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems0
        - $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems1
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4Items:
      type: object
      properties:
        content:
          type: array
          items:
            $ref: >-
              #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4ItemsContentItems
      required:
        - content
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInput4:
      type: array
      items:
        $ref: >-
          #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInputOneOf4Items
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaInput:
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
        - $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaInput4
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaEncodingFormat:
      type: string
      enum:
        - value: float
        - value: base64
    DataCollection:
      type: string
      enum:
        - value: deny
        - value: allow
    ProviderName:
      type: string
      enum:
        - value: AnyScale
        - value: Cent-ML
        - value: HuggingFace
        - value: Hyperbolic 2
        - value: Lepton
        - value: Lynn 2
        - value: Lynn
        - value: Mancer
        - value: Modal
        - value: OctoAI
        - value: Recursal
        - value: Reflection
        - value: Replicate
        - value: SambaNova 2
        - value: SF Compute
        - value: Together 2
        - value: 01.AI
        - value: AI21
        - value: AionLabs
        - value: Alibaba
        - value: Amazon Bedrock
        - value: Anthropic
        - value: Arcee
        - value: AtlasCloud
        - value: Atoma
        - value: Avian
        - value: Azure
        - value: BaseTen
        - value: Cerebras
        - value: Chutes
        - value: Cirrascale
        - value: Clarifai
        - value: Cloudflare
        - value: Cohere
        - value: CrofAI
        - value: Crusoe
        - value: DeepInfra
        - value: DeepSeek
        - value: Enfer
        - value: Featherless
        - value: Fireworks
        - value: Friendli
        - value: GMICloud
        - value: Google
        - value: Google AI Studio
        - value: Groq
        - value: Hyperbolic
        - value: Inception
        - value: InferenceNet
        - value: Infermatic
        - value: Inflection
        - value: InoCloud
        - value: Kluster
        - value: Lambda
        - value: Liquid
        - value: Mancer 2
        - value: Meta
        - value: Minimax
        - value: ModelRun
        - value: Mistral
        - value: Modular
        - value: Moonshot AI
        - value: Morph
        - value: NCompass
        - value: Nebius
        - value: NextBit
        - value: Nineteen
        - value: Novita
        - value: Nvidia
        - value: OpenAI
        - value: OpenInference
        - value: Parasail
        - value: Perplexity
        - value: Phala
        - value: Relace
        - value: SambaNova
        - value: SiliconFlow
        - value: Stealth
        - value: Switchpoint
        - value: Targon
        - value: Together
        - value: Ubicloud
        - value: Venice
        - value: WandB
        - value: xAI
        - value: Z.AI
        - value: FakeProvider
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderOrderItems:
      oneOf:
        - $ref: '#/components/schemas/ProviderName'
        - type: string
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderOnlyItems:
      oneOf:
        - $ref: '#/components/schemas/ProviderName'
        - type: string
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderIgnoreItems:
      oneOf:
        - $ref: '#/components/schemas/ProviderName'
        - type: string
    Quantization:
      type: string
      enum:
        - value: int4
        - value: int8
        - value: fp4
        - value: fp6
        - value: fp8
        - value: fp16
        - value: bf16
        - value: fp32
        - value: unknown
    ProviderSort:
      type: string
      enum:
        - value: price
        - value: throughput
        - value: latency
    BigNumberUnion:
      oneOf:
        - type: number
          format: double
        - type: string
        - type: number
          format: double
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderMaxPrice:
      type: object
      properties:
        prompt:
          $ref: '#/components/schemas/BigNumberUnion'
        completion:
          $ref: '#/components/schemas/BigNumberUnion'
        image:
          $ref: '#/components/schemas/BigNumberUnion'
        audio:
          $ref: '#/components/schemas/BigNumberUnion'
        request:
          $ref: '#/components/schemas/BigNumberUnion'
    EmbeddingsPostRequestBodyContentApplicationJsonSchemaProvider:
      type: object
      properties:
        allow_fallbacks:
          type:
            - boolean
            - 'null'
        require_parameters:
          type:
            - boolean
            - 'null'
        data_collection:
          $ref: '#/components/schemas/DataCollection'
        zdr:
          type:
            - boolean
            - 'null'
        enforce_distillable_text:
          type:
            - boolean
            - 'null'
        order:
          type:
            - array
            - 'null'
          items:
            $ref: >-
              #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderOrderItems
        only:
          type:
            - array
            - 'null'
          items:
            $ref: >-
              #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderOnlyItems
        ignore:
          type:
            - array
            - 'null'
          items:
            $ref: >-
              #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderIgnoreItems
        quantizations:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/Quantization'
        sort:
          $ref: '#/components/schemas/ProviderSort'
        max_price:
          $ref: >-
            #/components/schemas/EmbeddingsPostRequestBodyContentApplicationJsonSchemaProviderMaxPrice
    EmbeddingsPostResponsesContentApplicationJsonSchemaObject:
      type: string
      enum:
        - value: list
    EmbeddingsPostResponsesContentApplicationJsonSchemaDataItemsObject:
      type: string
      enum:
        - value: embedding
    EmbeddingsPostResponsesContentApplicationJsonSchemaDataItemsEmbedding:
      oneOf:
        - type: array
          items:
            type: number
            format: double
        - type: string
    EmbeddingsPostResponsesContentApplicationJsonSchemaDataItems:
      type: object
      properties:
        object:
          $ref: >-
            #/components/schemas/EmbeddingsPostResponsesContentApplicationJsonSchemaDataItemsObject
        embedding:
          $ref: >-
            #/components/schemas/EmbeddingsPostResponsesContentApplicationJsonSchemaDataItemsEmbedding
        index:
          type: number
          format: double
      required:
        - object
        - embedding
    EmbeddingsPostResponsesContentApplicationJsonSchemaUsage:
      type: object
      properties:
        prompt_tokens:
          type: number
          format: double
        total_tokens:
          type: number
          format: double
        cost:
          type: number
          format: double
      required:
        - prompt_tokens
        - total_tokens
    Embeddings_createEmbeddings_Response_200:
      type: object
      properties:
        id:
          type: string
        object:
          $ref: >-
            #/components/schemas/EmbeddingsPostResponsesContentApplicationJsonSchemaObject
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/EmbeddingsPostResponsesContentApplicationJsonSchemaDataItems
        model:
          type: string
        usage:
          $ref: >-
            #/components/schemas/EmbeddingsPostResponsesContentApplicationJsonSchemaUsage
      required:
        - object
        - data
        - model

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/embeddings"

payload = {
    "input": "string",
    "model": "string"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/embeddings';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"input":"string","model":"string"}'
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

	url := "https://openrouter.ai/api/v1/embeddings"

	payload := strings.NewReader("{\n  \"input\": \"string\",\n  \"model\": \"string\"\n}")

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

url = URI("https://openrouter.ai/api/v1/embeddings")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"input\": \"string\",\n  \"model\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/embeddings")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"input\": \"string\",\n  \"model\": \"string\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/embeddings', [
  'body' => '{
  "input": "string",
  "model": "string"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/embeddings");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"input\": \"string\",\n  \"model\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "input": "string",
  "model": "string"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/embeddings")! as URL,
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