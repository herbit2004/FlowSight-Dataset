# List all endpoints for a model

GET https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: List all endpoints for a model
  version: endpoint_endpoints.listEndpoints
paths:
  /models/{author}/{slug}/endpoints:
    get:
      operationId: list-endpoints
      summary: List all endpoints for a model
      tags:
        - - subpackage_endpoints
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
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Returns a list of endpoints
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Endpoints_listEndpoints_Response_200'
        '404':
          description: Not Found - Model does not exist
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
components:
  schemas:
    ModelGroup:
      type: string
      enum:
        - value: Router
        - value: Media
        - value: Other
        - value: GPT
        - value: Claude
        - value: Gemini
        - value: Grok
        - value: Cohere
        - value: Nova
        - value: Qwen
        - value: Yi
        - value: DeepSeek
        - value: Mistral
        - value: Llama2
        - value: Llama3
        - value: Llama4
        - value: PaLM
        - value: RWKV
        - value: Qwen3
    ModelArchitectureInstructType:
      type: string
      enum:
        - value: none
        - value: airoboros
        - value: alpaca
        - value: alpaca-modif
        - value: chatml
        - value: claude
        - value: code-llama
        - value: gemma
        - value: llama2
        - value: llama3
        - value: mistral
        - value: nemotron
        - value: neural
        - value: openchat
        - value: phi3
        - value: rwkv
        - value: vicuna
        - value: zephyr
        - value: deepseek-r1
        - value: deepseek-v3.1
        - value: qwq
        - value: qwen3
    InputModality:
      type: string
      enum:
        - value: text
        - value: image
        - value: file
        - value: audio
        - value: video
    OutputModality:
      type: string
      enum:
        - value: text
        - value: image
        - value: embeddings
    ListEndpointsResponseArchitectureTokenizer:
      type: object
      properties: {}
    InstructType:
      type: string
      enum:
        - value: none
        - value: airoboros
        - value: alpaca
        - value: alpaca-modif
        - value: chatml
        - value: claude
        - value: code-llama
        - value: gemma
        - value: llama2
        - value: llama3
        - value: mistral
        - value: nemotron
        - value: neural
        - value: openchat
        - value: phi3
        - value: rwkv
        - value: vicuna
        - value: zephyr
        - value: deepseek-r1
        - value: deepseek-v3.1
        - value: qwq
        - value: qwen3
    ListEndpointsResponseArchitecture:
      type: object
      properties:
        tokenizer:
          $ref: '#/components/schemas/ListEndpointsResponseArchitectureTokenizer'
        instruct_type:
          $ref: '#/components/schemas/InstructType'
        modality:
          type:
            - string
            - 'null'
        input_modalities:
          type: array
          items:
            $ref: '#/components/schemas/InputModality'
        output_modalities:
          type: array
          items:
            $ref: '#/components/schemas/OutputModality'
      required:
        - modality
        - input_modalities
        - output_modalities
        - tokenizer
        - instruct_type
    BigNumberUnion:
      oneOf:
        - type: number
          format: double
        - type: string
        - type: number
          format: double
    PublicEndpointPricing:
      type: object
      properties:
        prompt:
          $ref: '#/components/schemas/BigNumberUnion'
        completion:
          $ref: '#/components/schemas/BigNumberUnion'
        request:
          $ref: '#/components/schemas/BigNumberUnion'
        image:
          $ref: '#/components/schemas/BigNumberUnion'
        image_output:
          $ref: '#/components/schemas/BigNumberUnion'
        audio:
          $ref: '#/components/schemas/BigNumberUnion'
        input_audio_cache:
          $ref: '#/components/schemas/BigNumberUnion'
        web_search:
          $ref: '#/components/schemas/BigNumberUnion'
        internal_reasoning:
          $ref: '#/components/schemas/BigNumberUnion'
        input_cache_read:
          $ref: '#/components/schemas/BigNumberUnion'
        input_cache_write:
          $ref: '#/components/schemas/BigNumberUnion'
        discount:
          type: number
          format: double
      required:
        - prompt
        - completion
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
    PublicEndpointQuantization:
      type: object
      properties: {}
    Parameter:
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
    EndpointStatus:
      type: string
      enum:
        - value: '0'
        - value: '-1'
        - value: '-2'
        - value: '-3'
        - value: '-5'
        - value: '-10'
    PublicEndpoint:
      type: object
      properties:
        name:
          type: string
        model_name:
          type: string
        context_length:
          type: number
          format: double
        pricing:
          $ref: '#/components/schemas/PublicEndpointPricing'
        provider_name:
          $ref: '#/components/schemas/ProviderName'
        tag:
          type: string
        quantization:
          $ref: '#/components/schemas/PublicEndpointQuantization'
        max_completion_tokens:
          type:
            - number
            - 'null'
          format: double
        max_prompt_tokens:
          type:
            - number
            - 'null'
          format: double
        supported_parameters:
          type: array
          items:
            $ref: '#/components/schemas/Parameter'
        status:
          $ref: '#/components/schemas/EndpointStatus'
        uptime_last_30m:
          type:
            - number
            - 'null'
          format: double
        supports_implicit_caching:
          type: boolean
      required:
        - name
        - model_name
        - context_length
        - pricing
        - provider_name
        - tag
        - quantization
        - max_completion_tokens
        - max_prompt_tokens
        - supported_parameters
        - uptime_last_30m
        - supports_implicit_caching
    ListEndpointsResponse:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        created:
          type: number
          format: double
        description:
          type: string
        architecture:
          $ref: '#/components/schemas/ListEndpointsResponseArchitecture'
        endpoints:
          type: array
          items:
            $ref: '#/components/schemas/PublicEndpoint'
      required:
        - id
        - name
        - created
        - description
        - architecture
        - endpoints
    Endpoints_listEndpoints_Response_200:
      type: object
      properties:
        data:
          $ref: '#/components/schemas/ListEndpointsResponse'
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/models/author/slug/endpoints"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/models/author/slug/endpoints';
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

	url := "https://openrouter.ai/api/v1/models/author/slug/endpoints"

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

url = URI("https://openrouter.ai/api/v1/models/author/slug/endpoints")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/models/author/slug/endpoints")
  .header("Authorization", "Bearer <token>")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/models/author/slug/endpoints', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/models/author/slug/endpoints");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/models/author/slug/endpoints")! as URL,
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