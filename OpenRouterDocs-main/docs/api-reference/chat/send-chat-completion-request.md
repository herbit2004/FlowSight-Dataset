# Create a chat completion

POST https://openrouter.ai/api/v1/chat/completions
Content-Type: application/json

Sends a request for a model response for the given chat conversation. Supports both streaming and non-streaming modes.

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create a chat completion
  version: endpoint_chat.sendChatCompletionRequest
paths:
  /chat/completions:
    post:
      operationId: send-chat-completion-request
      summary: Create a chat completion
      description: >-
        Sends a request for a model response for the given chat conversation.
        Supports both streaming and non-streaming modes.
      tags:
        - - subpackage_chat
      parameters:
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful chat completion response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatResponse'
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
        description: Chat completion request parameters
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatGenerationParams'
components:
  schemas:
    ChatMessageContentItemText:
      type: object
      properties:
        type:
          type: string
          enum:
            - &ref_0
              type: stringLiteral
              value: text
        text:
          type: string
      required:
        - type
        - text
    SystemMessageContent1:
      type: array
      items:
        $ref: '#/components/schemas/ChatMessageContentItemText'
    SystemMessageContent:
      oneOf:
        - type: string
        - $ref: '#/components/schemas/SystemMessageContent1'
    SystemMessage:
      type: object
      properties:
        role:
          type: string
          enum:
            - type: stringLiteral
              value: system
        content:
          $ref: '#/components/schemas/SystemMessageContent'
        name:
          type: string
      required:
        - role
        - content
    ChatMessageContentItemImageImageUrlDetail:
      type: string
      enum:
        - value: auto
        - value: low
        - value: high
    ChatMessageContentItemImageImageUrl:
      type: object
      properties:
        url:
          type: string
        detail:
          $ref: '#/components/schemas/ChatMessageContentItemImageImageUrlDetail'
      required:
        - url
    ChatMessageContentItemAudioInputAudioFormat:
      type: string
      enum:
        - value: wav
        - value: mp3
        - value: flac
        - value: m4a
        - value: ogg
        - value: pcm16
        - value: pcm24
    ChatMessageContentItemAudioInputAudio:
      type: object
      properties:
        data:
          type: string
        format:
          $ref: '#/components/schemas/ChatMessageContentItemAudioInputAudioFormat'
      required:
        - data
        - format
    ChatMessageContentItemVideoOneOf0VideoUrl:
      type: object
      properties:
        url:
          type: string
      required:
        - url
    ChatMessageContentItemVideo0:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: input_video
        video_url:
          $ref: '#/components/schemas/ChatMessageContentItemVideoOneOf0VideoUrl'
      required:
        - type
        - video_url
    ChatMessageContentItemVideoOneOf1VideoUrl:
      type: object
      properties:
        url:
          type: string
      required:
        - url
    ChatMessageContentItemVideo1:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: video_url
        video_url:
          $ref: '#/components/schemas/ChatMessageContentItemVideoOneOf1VideoUrl'
      required:
        - type
        - video_url
    ChatMessageContentItem:
      oneOf:
        - type: object
          properties:
            type:
              type: string
              enum:
                - *ref_0
            text:
              type: string
          required:
            - type
            - text
          description: text variant
        - type: object
          properties:
            type:
              type: string
              enum:
                - type: stringLiteral
                  value: image_url
            image_url:
              $ref: '#/components/schemas/ChatMessageContentItemImageImageUrl'
          required:
            - type
            - image_url
          description: image_url variant
        - type: object
          properties:
            type:
              type: string
              enum:
                - type: stringLiteral
                  value: input_audio
            input_audio:
              $ref: '#/components/schemas/ChatMessageContentItemAudioInputAudio'
          required:
            - type
            - input_audio
          description: input_audio variant
        - type: object
          properties:
            type:
              type: string
              enum:
                - input_video
              description: 'Discriminator value: input_video'
          required:
            - type
          description: input_video variant
        - type: object
          properties:
            type:
              type: string
              enum:
                - video_url
              description: 'Discriminator value: video_url'
          required:
            - type
          description: video_url variant
      discriminator:
        propertyName: type
    UserMessageContent1:
      type: array
      items:
        $ref: '#/components/schemas/ChatMessageContentItem'
    UserMessageContent:
      oneOf:
        - type: string
        - $ref: '#/components/schemas/UserMessageContent1'
    UserMessage:
      type: object
      properties:
        role:
          type: string
          enum:
            - type: stringLiteral
              value: user
        content:
          $ref: '#/components/schemas/UserMessageContent'
        name:
          type: string
      required:
        - role
        - content
    MessageOneOf2Content1:
      type: array
      items:
        $ref: '#/components/schemas/ChatMessageContentItemText'
    MessageOneOf2Content:
      oneOf:
        - type: string
        - $ref: '#/components/schemas/MessageOneOf2Content1'
    Message2:
      type: object
      properties:
        role:
          type: string
          enum:
            - type: stringLiteral
              value: developer
        content:
          $ref: '#/components/schemas/MessageOneOf2Content'
        name:
          type: string
      required:
        - role
        - content
    AssistantMessageContent1:
      type: array
      items:
        $ref: '#/components/schemas/ChatMessageContentItem'
    AssistantMessageContent:
      oneOf:
        - type: string
        - $ref: '#/components/schemas/AssistantMessageContent1'
    ChatMessageToolCallFunction:
      type: object
      properties:
        name:
          type: string
        arguments:
          type: string
      required:
        - name
        - arguments
    ChatMessageToolCall:
      type: object
      properties:
        id:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: function
        function:
          $ref: '#/components/schemas/ChatMessageToolCallFunction'
      required:
        - id
        - type
        - function
    AssistantMessage:
      type: object
      properties:
        role:
          type: string
          enum:
            - type: stringLiteral
              value: assistant
        content:
          oneOf:
            - $ref: '#/components/schemas/AssistantMessageContent'
            - type: 'null'
        name:
          type: string
        tool_calls:
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageToolCall'
        refusal:
          type:
            - string
            - 'null'
        reasoning:
          type:
            - string
            - 'null'
      required:
        - role
    ToolResponseMessageContent1:
      type: array
      items:
        $ref: '#/components/schemas/ChatMessageContentItem'
    ToolResponseMessageContent:
      oneOf:
        - type: string
        - $ref: '#/components/schemas/ToolResponseMessageContent1'
    ToolResponseMessage:
      type: object
      properties:
        role:
          type: string
          enum:
            - type: stringLiteral
              value: tool
        content:
          $ref: '#/components/schemas/ToolResponseMessageContent'
        tool_call_id:
          type: string
      required:
        - role
        - content
        - tool_call_id
    Message:
      oneOf:
        - $ref: '#/components/schemas/SystemMessage'
        - $ref: '#/components/schemas/UserMessage'
        - $ref: '#/components/schemas/Message2'
        - $ref: '#/components/schemas/AssistantMessage'
        - $ref: '#/components/schemas/ToolResponseMessage'
    ModelName:
      type: string
    ChatGenerationParamsReasoningEffort:
      type: string
      enum:
        - value: minimal
        - value: low
        - value: medium
        - value: high
    ReasoningSummaryVerbosity:
      type: string
      enum:
        - value: auto
        - value: concise
        - value: detailed
    ChatGenerationParamsReasoning:
      type: object
      properties:
        effort:
          oneOf:
            - $ref: '#/components/schemas/ChatGenerationParamsReasoningEffort'
            - type: 'null'
        summary:
          oneOf:
            - $ref: '#/components/schemas/ReasoningSummaryVerbosity'
            - type: 'null'
    ChatGenerationParamsResponseFormat0:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
      required:
        - type
    ChatGenerationParamsResponseFormat1:
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
    ChatGenerationParamsResponseFormat4:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: python
      required:
        - type
    ChatGenerationParamsResponseFormat:
      oneOf:
        - $ref: '#/components/schemas/ChatGenerationParamsResponseFormat0'
        - $ref: '#/components/schemas/ChatGenerationParamsResponseFormat1'
        - $ref: '#/components/schemas/ResponseFormatJSONSchema'
        - $ref: '#/components/schemas/ResponseFormatTextGrammar'
        - $ref: '#/components/schemas/ChatGenerationParamsResponseFormat4'
    ChatGenerationParamsStop:
      oneOf:
        - type: string
        - type: array
          items:
            type: string
    ChatStreamOptions:
      type: object
      properties:
        include_usage:
          type: boolean
    NamedToolChoiceFunction:
      type: object
      properties:
        name:
          type: string
      required:
        - name
    NamedToolChoice:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: function
        function:
          $ref: '#/components/schemas/NamedToolChoiceFunction'
      required:
        - type
        - function
    ToolChoiceOption:
      oneOf:
        - type: string
          enum:
            - type: stringLiteral
              value: none
        - type: string
          enum:
            - type: stringLiteral
              value: auto
        - type: string
          enum:
            - type: stringLiteral
              value: required
        - $ref: '#/components/schemas/NamedToolChoice'
    ToolDefinitionJsonFunction:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        parameters:
          type: object
          additionalProperties:
            description: Any type
        strict:
          type:
            - boolean
            - 'null'
      required:
        - name
    ToolDefinitionJson:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: function
        function:
          $ref: '#/components/schemas/ToolDefinitionJsonFunction'
      required:
        - type
        - function
    ChatGenerationParams:
      type: object
      properties:
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
        model:
          $ref: '#/components/schemas/ModelName'
        models:
          type: array
          items:
            $ref: '#/components/schemas/ModelName'
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
            - boolean
            - 'null'
        top_logprobs:
          type:
            - number
            - 'null'
          format: double
        max_completion_tokens:
          type:
            - number
            - 'null'
          format: double
        max_tokens:
          type:
            - number
            - 'null'
          format: double
        metadata:
          type: object
          additionalProperties:
            type: string
        presence_penalty:
          type:
            - number
            - 'null'
          format: double
        reasoning:
          $ref: '#/components/schemas/ChatGenerationParamsReasoning'
        response_format:
          $ref: '#/components/schemas/ChatGenerationParamsResponseFormat'
        seed:
          type:
            - integer
            - 'null'
        stop:
          oneOf:
            - $ref: '#/components/schemas/ChatGenerationParamsStop'
            - type: 'null'
        stream:
          type: boolean
        stream_options:
          oneOf:
            - $ref: '#/components/schemas/ChatStreamOptions'
            - type: 'null'
        temperature:
          type:
            - number
            - 'null'
          format: double
        tool_choice:
          $ref: '#/components/schemas/ToolChoiceOption'
        tools:
          type: array
          items:
            $ref: '#/components/schemas/ToolDefinitionJson'
        top_p:
          type:
            - number
            - 'null'
          format: double
        user:
          type: string
      required:
        - messages
    ChatCompletionFinishReason:
      type: string
      enum:
        - value: tool_calls
        - value: stop
        - value: length
        - value: content_filter
        - value: error
    __schema0:
      oneOf:
        - $ref: '#/components/schemas/ChatCompletionFinishReason'
        - type: 'null'
    ChatMessageTokenLogprobTopLogprobsItems:
      type: object
      properties:
        token:
          type: string
        logprob:
          type: number
          format: double
        bytes:
          type:
            - array
            - 'null'
          items:
            type: number
            format: double
      required:
        - token
        - logprob
        - bytes
    ChatMessageTokenLogprob:
      type: object
      properties:
        token:
          type: string
        logprob:
          type: number
          format: double
        bytes:
          type:
            - array
            - 'null'
          items:
            type: number
            format: double
        top_logprobs:
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobTopLogprobsItems'
      required:
        - token
        - logprob
        - bytes
        - top_logprobs
    ChatMessageTokenLogprobs:
      type: object
      properties:
        content:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprob'
        refusal:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprob'
      required:
        - content
        - refusal
    ChatResponseChoice:
      type: object
      properties:
        finish_reason:
          $ref: '#/components/schemas/__schema0'
        index:
          type: number
          format: double
        message:
          $ref: '#/components/schemas/AssistantMessage'
        logprobs:
          oneOf:
            - $ref: '#/components/schemas/ChatMessageTokenLogprobs'
            - type: 'null'
      required:
        - finish_reason
        - index
        - message
    ChatGenerationTokenUsageCompletionTokensDetails:
      type: object
      properties:
        reasoning_tokens:
          type:
            - number
            - 'null'
          format: double
        audio_tokens:
          type:
            - number
            - 'null'
          format: double
        accepted_prediction_tokens:
          type:
            - number
            - 'null'
          format: double
        rejected_prediction_tokens:
          type:
            - number
            - 'null'
          format: double
    ChatGenerationTokenUsagePromptTokensDetails:
      type: object
      properties:
        cached_tokens:
          type: number
          format: double
        audio_tokens:
          type: number
          format: double
        video_tokens:
          type: number
          format: double
    ChatGenerationTokenUsage:
      type: object
      properties:
        completion_tokens:
          type: number
          format: double
        prompt_tokens:
          type: number
          format: double
        total_tokens:
          type: number
          format: double
        completion_tokens_details:
          oneOf:
            - $ref: >-
                #/components/schemas/ChatGenerationTokenUsageCompletionTokensDetails
            - type: 'null'
        prompt_tokens_details:
          oneOf:
            - $ref: '#/components/schemas/ChatGenerationTokenUsagePromptTokensDetails'
            - type: 'null'
      required:
        - completion_tokens
        - prompt_tokens
        - total_tokens
    ChatResponse:
      type: object
      properties:
        id:
          type: string
        choices:
          type: array
          items:
            $ref: '#/components/schemas/ChatResponseChoice'
        created:
          type: number
          format: double
        model:
          type: string
        object:
          type: string
          enum:
            - type: stringLiteral
              value: chat.completion
        system_fingerprint:
          type:
            - string
            - 'null'
        usage:
          $ref: '#/components/schemas/ChatGenerationTokenUsage'
      required:
        - id
        - choices
        - created
        - model
        - object

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/chat/completions"

payload = { "messages": [
        {
            "role": "string",
            "content": "string"
        }
    ] }
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/chat/completions';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"messages":[{"role":"string","content":"string"}]}'
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

	url := "https://openrouter.ai/api/v1/chat/completions"

	payload := strings.NewReader("{\n  \"messages\": [\n    {\n      \"role\": \"string\",\n      \"content\": \"string\"\n    }\n  ]\n}")

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

url = URI("https://openrouter.ai/api/v1/chat/completions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"messages\": [\n    {\n      \"role\": \"string\",\n      \"content\": \"string\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/chat/completions")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"messages\": [\n    {\n      \"role\": \"string\",\n      \"content\": \"string\"\n    }\n  ]\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/chat/completions', [
  'body' => '{
  "messages": [
    {
      "role": "string",
      "content": "string"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/chat/completions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"messages\": [\n    {\n      \"role\": \"string\",\n      \"content\": \"string\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = ["messages": [
    [
      "role": "string",
      "content": "string"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/chat/completions")! as URL,
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