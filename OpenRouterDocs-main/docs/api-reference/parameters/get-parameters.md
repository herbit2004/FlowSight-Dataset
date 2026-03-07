# Get a model's supported parameters and data about which are most popular

GET https://openrouter.ai/api/v1/parameters/{author}/{slug}

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Get a model's supported parameters and data about which are most popular
  version: endpoint_parameters.getParameters
paths:
  /parameters/{author}/{slug}:
    get:
      operationId: get-parameters
      summary: Get a model's supported parameters and data about which are most popular
      tags:
        - - subpackage_parameters
      parameters:
        - name: author
          in: path
          required: true
          schema:
            type: string
        - name: slug
          in: path
          required: true
          schema:
            type: string
        - name: provider
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/ParametersAuthorSlugGetParametersProvider'
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Returns the parameters for the specified model
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Parameters_getParameters_Response_200'
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '404':
          description: Not Found - Model or provider does not exist
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
components:
  schemas:
    ParametersAuthorSlugGetParametersProvider:
      type: string
      enum:
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
    ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaDataSupportedParametersItems:
      type: string
      enum:
        - value: temperature
        - value: top_p
        - value: top_k
        - value: min_p
        - value: top_a
        - value: frequency_penalty
        - value: presence_penalty
        - value: repetition_penalty
        - value: max_tokens
        - value: logit_bias
        - value: logprobs
        - value: top_logprobs
        - value: seed
        - value: response_format
        - value: structured_outputs
        - value: stop
        - value: tools
        - value: tool_choice
        - value: parallel_tool_calls
        - value: include_reasoning
        - value: reasoning
        - value: web_search_options
        - value: verbosity
    ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        model:
          type: string
        supported_parameters:
          type: array
          items:
            $ref: >-
              #/components/schemas/ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaDataSupportedParametersItems
      required:
        - model
        - supported_parameters
    Parameters_getParameters_Response_200:
      type: object
      properties:
        data:
          $ref: >-
            #/components/schemas/ParametersAuthorSlugGetResponsesContentApplicationJsonSchemaData
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/parameters/author/slug"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/parameters/author/slug';
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

	url := "https://openrouter.ai/api/v1/parameters/author/slug"

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

url = URI("https://openrouter.ai/api/v1/parameters/author/slug")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/parameters/author/slug")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/parameters/author/slug', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/parameters/author/slug");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/parameters/author/slug")! as URL,
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