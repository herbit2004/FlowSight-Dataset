# Exchange authorization code for API key

POST https://openrouter.ai/api/v1/auth/keys
Content-Type: application/json

Exchange an authorization code from the PKCE flow for a user-controlled API key

## OpenAPI Specification

```yaml
openapi: 3.1.1
info:
  title: Exchange authorization code for API key
  version: endpoint_oAuth.exchangeAuthCodeForAPIKey
paths:
  /auth/keys:
    post:
      operationId: exchange-auth-code-for-api-key
      summary: Exchange authorization code for API key
      description: >-
        Exchange an authorization code from the PKCE flow for a user-controlled
        API key
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
          description: Successfully exchanged code for an API key
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/OAuth_exchangeAuthCodeForAPIKey_Response_200
        '400':
          description: Bad Request - Invalid request parameters or malformed input
          content: {}
        '403':
          description: Forbidden - Authentication successful but insufficient permissions
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
                code:
                  type: string
                code_verifier:
                  type: string
                code_challenge_method:
                  oneOf:
                    - $ref: >-
                        #/components/schemas/AuthKeysPostRequestBodyContentApplicationJsonSchemaCodeChallengeMethod
                    - type: 'null'
              required:
                - code
components:
  schemas:
    AuthKeysPostRequestBodyContentApplicationJsonSchemaCodeChallengeMethod:
      type: string
      enum:
        - value: S256
        - value: plain
    OAuth_exchangeAuthCodeForAPIKey_Response_200:
      type: object
      properties:
        key:
          type: string
        user_id:
          type:
            - string
            - 'null'
      required:
        - key
        - user_id

```

## SDK Code Examples

```python
import requests

url = "https://openrouter.ai/api/v1/auth/keys"

payload = {
    "code": "auth_code_abc123def456",
    "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
    "code_challenge_method": "S256"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://openrouter.ai/api/v1/auth/keys';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"code":"auth_code_abc123def456","code_verifier":"dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk","code_challenge_method":"S256"}'
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

	url := "https://openrouter.ai/api/v1/auth/keys"

	payload := strings.NewReader("{\n  \"code\": \"auth_code_abc123def456\",\n  \"code_verifier\": \"dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk\",\n  \"code_challenge_method\": \"S256\"\n}")

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

url = URI("https://openrouter.ai/api/v1/auth/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"code\": \"auth_code_abc123def456\",\n  \"code_verifier\": \"dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk\",\n  \"code_challenge_method\": \"S256\"\n}"

response = http.request(request)
puts response.read_body
```

```java
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/auth/keys")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"code\": \"auth_code_abc123def456\",\n  \"code_verifier\": \"dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk\",\n  \"code_challenge_method\": \"S256\"\n}")
  .asString();
```

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/auth/keys', [
  'body' => '{
  "code": "auth_code_abc123def456",
  "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
  "code_challenge_method": "S256"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
var client = new RestClient("https://openrouter.ai/api/v1/auth/keys");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"code\": \"auth_code_abc123def456\",\n  \"code_verifier\": \"dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk\",\n  \"code_challenge_method\": \"S256\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "code": "auth_code_abc123def456",
  "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
  "code_challenge_method": "S256"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/auth/keys")! as URL,
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