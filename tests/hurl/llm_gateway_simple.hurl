POST http://localhost:12000/v1/chat/completions
Content-Type: application/json

{
  "model": "--",
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
  "stream": true
}
