import os
from datetime import date

from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

router = APIRouter()


class ConversationMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    previous_messages: list[ConversationMessage]
    question: str


__allowed_roles = ["user", "assistant"]

client = AsyncOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.environ["TOGETHER_API_KEY"],
)


@router.post("/chat")
async def chat(chat_request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": "You're an assistant that helps university students at Cardiff University."  # noqa
                       " You can help me by answering my questions."
                       " You can also ask me questions."
                       f"\nCurrent Date: {date.today()}"
        }
    ]

    for message in chat_request.previous_messages:
        if message.role not in __allowed_roles:
            raise ValueError(f"Role {message.role} is not allowed")

        messages.append(message.model_dump())

    messages.append({
        "role": "user",
        "content": chat_request.question
    })

    response = await client.chat.completions.create(
        messages=messages,
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        stream=True
    )

    async def event_generator():
        async for event in response:
            choice = event.choices[0]
            delta = choice.delta
            content = delta.content
            if content is not None:
                yield {
                    "text": delta.content
                }

    return EventSourceResponse(event_generator())
