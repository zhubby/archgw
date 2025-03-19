import logging
import json
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionsRequest(BaseModel):
    messages: List[Message]
    model: str
    metadata: Dict[str, Any] = {}
    stream: bool = False


openai_client = openai.OpenAI(
    api_key="None",  # archgw picks the API key from the config file
    base_url="http://host.docker.internal:12000/v1",
)


def call_openai(messages: List[Dict[str, str]], stream: bool):
    completion = openai_client.chat.completions.create(
        model="None",  # archgw picks the default LLM configured in the config file
        messages=messages,
        stream=stream,
    )

    if stream:

        def stream():
            for line in completion:
                if line.choices and len(line.choices) > 0 and line.choices[0].delta:
                    chunk_response_str = json.dumps(line.model_dump())
                    yield "data: " + chunk_response_str + "\n\n"
            yield "data: [DONE]" + "\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")
    else:
        return completion


class Agent:
    def __init__(self, role: str, instructions: str):
        self.system_prompt = f"You are a {role}.\n{instructions}"

    def handle(self, req: ChatCompletionsRequest):
        messages = [{"role": "system", "content": self.get_system_prompt()}] + [
            message.model_dump() for message in req.messages
        ]
        return call_openai(messages, req.stream)

    def get_system_prompt(self) -> str:
        return self.system_prompt


# Define your agents
AGENTS = {
    "sales_agent": Agent(
        role="sales agent",
        instructions=(
            "Always answer in a sentence or less.\n"
            "Follow the following routine with the user:\n"
            "1. Engage\n"
            "2. Quote ridiculous price\n"
            "3. Reveal caveat if user agrees."
        ),
    ),
    "issues_and_repairs": Agent(
        role="issues and repairs agent",
        instructions="Propose a solution, offer refund if necessary.",
    ),
    "escalate_to_human": Agent(
        role="human escalation agent", instructions="Escalate issues to a human."
    ),
    "unknown_agent": Agent(
        role="general assistant", instructions="Assist the user in general queries."
    ),
}


@app.post("/v1/chat/completions")
def completion_api(req: ChatCompletionsRequest, request: Request):
    agent_name = req.metadata.get("agent-name", "unknown_agent")
    agent = AGENTS.get(agent_name)
    logger.info(f"Routing to agent: {agent_name}")

    return agent.handle(req)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
