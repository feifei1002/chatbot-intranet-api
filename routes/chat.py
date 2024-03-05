import json
import os
from datetime import date

from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

router = APIRouter()
#
# # local variable for chat history,
# # to be accessed in suggested_questions.py
# chat_history = []
#
#
# # function to set local variable when running post request /chat
# def get_history(x):
#     # global variable is bad practice so need to figure out better method
#     global chat_history
#     chat_history = x


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


class ChatHistory(BaseModel):
    chat_messages: list[ConversationMessage]
    question: str


__allowed_roles = ["user", "assistant"]

client = AsyncOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.environ["TOGETHER_API_KEY"],
)


@router.post("/chat_history")
async def get_chat_history(messages: ChatHistory):
    history = messages.chat_messages
    q = messages.question
    print("chat history is ", history)
    print("question is ", q)
#
# @router.post("/chat_history")
# async def chat_history(chat_request: ChatRequest):
#     # messages1 = [
#     #     {
#     #         "role": "system",
#     #         "content": "You're an assistant that helps university students at Cardiff University."  # noqa
#     #                    " You can help me by answering my questions."
#     #                    " You can also ask me questions."
#     #                    f"\nCurrent Date: {date.today()}"
#     #     }
#     # ]
#     #
#     # for message1 in chat_request.previous_messages:
#     #     if message1.role not in __allowed_roles:
#     #         raise ValueError(f"Role {message1.role} is not allowed")
#     #
#     #     messages1.append(message1.model_dump())
#     #
#     # # history = chat_request.previous_messages
#     # messages1.append({
#     #     "role": "user",
#     #     "content": chat_request.question
#     # })
#
#     messages1 = chat_request.previous_messages
#
#     print("history is: ", messages1)


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

    # # send chat history to suggested questions
    # get_history(messages)
    # print(chat_history)

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
