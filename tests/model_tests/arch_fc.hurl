POST https://archfc.katanemo.dev/v1/chat/completions
Content-Type: application/json

{
  "model": "Arch-Intent",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant.\n\nYou task is to check if there are any tools that can be used to help the last user message in conversations according to the available tools listed below.\n\n<tools>\n{\"index\": \"T0\", \"type\": \"function\", \"function\": {\"name\": \"weather_forecast\", \"parameters\": {\"type\": \"object\", \"properties\": {\"city\": {\"type\": \"str\"}, \"days\": {\"type\": \"int\"}}, \"required\": [\"city\", \"days\"]}}}\n</tools>\n\nProvide your tool assessment for ONLY THE LAST USER MESSAGE in the above conversation:\n- First line must read 'Yes' or 'No'.\n- If yes, a second line must include a comma-separated list of tool indexes.\n"
    },
    { "role": "user", "content": "how is the weather in seattle? Are there any tools can help?" }
  ],
  "stream": false
}

HTTP 200
[Asserts]
header "content-type" == "application/json"
jsonpath "$.model" matches /^Arch-Function/
jsonpath "$.usage" != null
jsonpath "$.choices[0].message.content" matches /Yes/
jsonpath "$.choices[0].message.role" == "assistant"
