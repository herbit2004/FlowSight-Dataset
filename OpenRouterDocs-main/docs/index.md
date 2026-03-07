# OpenRouter Quickstart Guide | Developer Documentation | OpenRouter | Documentation

**Source:** https://openrouter.ai/docs/

---

Overview
Quickstart
FAQ
Principles
Models
Enterprise
Features
Privacy and Logging
Zero Data Retention (ZDR)
Model Routing
Provider Routing
Exacto Variant
Latency and Performance
Presets
Prompt Caching
Structured Outputs
Tool Calling
Multimodal
Message Transforms
Uptime Optimization
Web Search
Zero Completion Insurance
Provisioning API Keys
App Attribution
API Reference
Overview
Streaming
Embeddings
Limits
Authentication
Parameters
Errors
Responses API
beta.responses
Analytics
Credits
Embeddings
Generations
Models
Endpoints
Parameters
Providers
API Keys
O Auth
Chat
Completions
SDK Reference (BETA)
Python SDK
TypeScript SDK
Use Cases
BYOK
Crypto API
OAuth PKCE
MCP Servers
Organization Management
For Providers
Reasoning Tokens
Usage Accounting
User Tracking
Community
Frameworks and Integrations Overview
Effect AI SDK
Arize
LangChain
LiveKit
Langfuse
Mastra
OpenAI SDK
PydanticAI
Vercel AI SDK
Xcode
Zapier
Discord
Light
On this page
Using the OpenRouter SDK (Beta)
Using the OpenRouter API directly
Using the OpenAI SDK
Using third-party SDKs
Overview
Quickstart
Copy page
Get started with OpenRouter
OpenRouter provides a unified API that gives you access to hundreds of AI models through a single endpoint, while automatically handling fallbacks and selecting the most cost-effective options. Get started with just a few lines of code using your preferred SDK or framework.
Looking for information about free models and rate limits? Please see the
FAQ
In the examples below, the OpenRouter-specific headers are optional. Setting them allows your app to appear on the OpenRouter leaderboards. For detailed information about app attribution, see our
App Attribution guide
.
Using the OpenRouter SDK (Beta)
First, install the SDK:
npm
yarn
pnpm
$
npm install @openrouter/sdk
Then use it in your code:
TypeScript SDK
1
import { OpenRouter } from '@openrouter/sdk';
2
3
const openRouter = new OpenRouter({
4
apiKey: '<OPENROUTER_API_KEY>',
5
defaultHeaders: {
6
'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
7
'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
8
},
9
});
10
11
const completion = await openRouter.chat.send({
12
model: 'openai/gpt-4o',
13
messages: [
14
{
15
role: 'user',
16
content: 'What is the meaning of life?',
17
},
18
],
19
stream: false,
20
});
21
22
console.log(completion.choices[0].message.content);
Using the OpenRouter API directly
You can use the interactive
Request Builder
to generate OpenRouter API requests in the language of your choice.
Python
TypeScript (fetch)
Shell
1
import requests
2
import json
3
4
response = requests.post(
5
url="https://openrouter.ai/api/v1/chat/completions",
6
headers={
7
"Authorization": "Bearer <OPENROUTER_API_KEY>",
8
"HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
9
"X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
10
},
11
data=json.dumps({
12
"model": "openai/gpt-4o", # Optional
13
"messages": [
14
{
15
"role": "user",
16
"content": "What is the meaning of life?"
17
}
18
]
19
})
20
)
Using the OpenAI SDK
Typescript
Python
1
import OpenAI from 'openai';
2
3
const openai = new OpenAI({
4
baseURL: 'https://openrouter.ai/api/v1',
5
apiKey: '<OPENROUTER_API_KEY>',
6
defaultHeaders: {
7
'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
8
'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
9
},
10
});
11
12
async function main() {
13
const completion = await openai.chat.completions.create({
14
model: 'openai/gpt-4o',
15
messages: [
16
{
17
role: 'user',
18
content: 'What is the meaning of life?',
19
},
20
],
21
});
22
23
console.log(completion.choices[0].message);
24
}
25
26
main();
The API also supports
streaming
.
Using third-party SDKs
For information about using third-party SDKs and frameworks with OpenRouter, please
see our frameworks documentation.
Was this page helpful?
Yes
No
Frequently Asked Questions
Common questions about OpenRouter
Next
Build with