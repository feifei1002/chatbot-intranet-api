import json
import os
from datetime import date

from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

router = APIRouter()


class ConversationMessage(BaseModel):
    """
    A message in a conversation
    """
    role: str
    content: str


class ChatRequest(BaseModel):
    """
    A request to the chat endpoint
    """
    previous_messages: list[ConversationMessage]
    question: str


# class ChatHistory(BaseModel):
#     chat_messages: list[ConversationMessage]


__allowed_roles = ["user", "assistant"]

client = AsyncOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.environ["TOGETHER_API_KEY"],
)


# @router.post("/chat_history")
# async def get_chat_history(messages: ChatHistory):
#     message_history = [
#         {
#             "role": "system",
#             "content": "You're an assistant that helps university students at Cardiff University."  # noqa
#                        " You can help me by answering my questions."
#                        " You can also ask me questions."
#                        f"\nCurrent Date: {date.today()}"
#         }
#     ]
#
#     for message in messages.chat_messages:
#         if message.role not in __allowed_roles:
#             raise ValueError(f"Role {message.role} is not allowed")
#
#         message_history.append(message.model_dump())
#
#     print("history is ", message_history)
#
#     return message_history


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

    # Check if the role for each message is allowed
    # this is to prevent the user from impersonating the system role function role, etc.
    for message in chat_request.previous_messages:
        if message.role not in __allowed_roles:
            raise ValueError(f"Role {message.role} is not allowed")

        messages.append(message.model_dump())

    # Add the user's question to the messages
    messages.append({
        "role": "user",
        "content": chat_request.question
    })

    # Create a chat completion request
    response = await client.chat.completions.create(
        messages=messages,
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        stream=True
    )

    # Create an event generator to stream the response from OpenAI's format
    async def event_generator():
        async for event in response:
            choice = event.choices[0]
            delta = choice.delta
            content = delta.content
            if content is not None:
                yield json.dumps({
                    "text": delta.content
                })

    return EventSourceResponse(event_generator())
