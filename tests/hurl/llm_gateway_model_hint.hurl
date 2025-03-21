POST http://localhost:12000/v1/chat/completions
Content-Type: application/json
x-arch-llm-provider-hint: gpt-4o

{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant.\n"
    },
    {
      "role": "user",
      "content": "I want to sell red shoes"
    }
  ],
  "stream": false
}

HTTP 200
[Asserts]
header "content-type" == "application/json"
jsonpath "$.model" matches /^gpt-4o-2/
jsonpath "$.usage" != null
jsonpath "$.choices[0].message.content" != null
jsonpath "$.choices[0].message.role" == "assistant"
