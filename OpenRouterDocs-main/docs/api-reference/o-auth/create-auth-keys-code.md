# Create authorization code

POST https://openrouter.ai/api/v1/auth/keys/code
Content-Type: application/json

Create an authorization code for the PKCE flow to generate a user-controlled API key

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Create authorization code
  version: endpoint_oAuth.createAuthKeysCode
paths:
  /auth/keys/code:
    post:
      operationId: create-auth-keys-code
      summary: Create authorization code
      description: >-
        Create an authorization code for the PKCE flow to generate a
        user-controlled API key
      tags:
        - - subpackage_oAuth
      parameters:
        - name: Authorization
          in: header
          description: API key as bearer token in Authorization header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully created authorization code
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OAuth_createAuthKeysCode_Response_200'
        '400':
          description: Bad Request - Invalid request parameters or malformed input
          content: {}
        '401':
          description: Unauthorized - Authentication required or invalid credentials
          content: {}
        '500':
          description: Internal Server Error - Unexpected server error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                callback_url:
                  type: string
                  format: uri
                code_challenge:
                  type: string
                code_challenge_method:
                  $ref: >-
                    #/components/schemas/AuthKeysCodePostRequestBodyContentApplicationJsonSchemaCodeChallengeMethod
                limit:
                  type: number
                  format: double
                expires_at:
                  type:
                    - string
                    - 'null'
                  format: date-time
              required:
                - callback_url
components:
  schemas:
    AuthKeysCodePostRequestBodyContentApplicationJsonSchemaCodeChallengeMethod:
      type: string
      enum:
        - value: S256
        - value: plain
    AuthKeysCodePostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        id:
          type: string
        app_id:
          type: number
          format: double
        created_at:
          type: string
      required:
        - id
        - app_id
        - created_at
    OAuth_createAuthKeysCode_Response_200:
      type: object
      properties:
        data:
          $ref: >-
            #/components/schemas/AuthKeysCodePostResponsesContentApplicationJsonSchemaData
      required:
        - data

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/auth/keys/code"

payload = {
    "callback_url": "https://myapp.com/auth/callback",
    "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    "code_challenge_method": "S256",
    "limit": 100
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/auth/keys/code';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"callback_url":"https://myapp.com/auth/callback","code_challenge":"E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM","code_challenge_method":"S256","limit":100}'
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

	url := "https://openrouter.ai/api/v1/auth/keys/code"

	payload := strings.NewReader("{\n  \"callback_url\": \"https://myapp.com/auth/callback\",\n  \"code_challenge\": \"E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM\",\n  \"code_challenge_method\": \"S256\",\n  \"limit\": 100\n}")

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

url = URI("https://openrouter.ai/api/v1/auth/keys/code")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"callback_url\": \"https://myapp.com/auth/callback\",\n  \"code_challenge\": \"E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM\",\n  \"code_challenge_method\": \"S256\",\n  \"limit\": 100\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/auth/keys/code")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"callback_url\": \"https://myapp.com/auth/callback\",\n  \"code_challenge\": \"E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM\",\n  \"code_challenge_method\": \"S256\",\n  \"limit\": 100\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/auth/keys/code', [
  'body' => '{
  "callback_url": "https://myapp.com/auth/callback",
  "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  "code_challenge_method": "S256",
  "limit": 100
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/auth/keys/code");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"callback_url\": \"https://myapp.com/auth/callback\",\n  \"code_challenge\": \"E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM\",\n  \"code_challenge_method\": \"S256\",\n  \"limit\": 100\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "callback_url": "https://myapp.com/auth/callback",
  "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  "code_challenge_method": "S256",
  "limit": 100
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/auth/keys/code")! as URL,
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