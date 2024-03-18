import os
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Response
from openai import AsyncOpenAI
from pydantic import BaseModel
from utils.db import pool
from utils.models import ConversationMessage

router = APIRouter()

# use api key to allow usage of TogetherAI
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )

__allowed_roles = ["user", "assistant"]


class ChatHistory(BaseModel):
    chat_messages: list[ConversationMessage]


async def create_conversation_title(message_history: list[dict]):
    messages = message_history.copy()

    # adds question prompt to ask for suggestions
    messages.append(
        {"role": "user",
         "content": "Based on the conversation so far, what is a title to summarise this conversation? "  # noqa
                    "Make sure to format in a JSON object with an array in the key 'title'."})  # noqa

    # gets response after asking openapi question
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=messages,
        response_format={
            "type": "json_object"
        }
    )

    print("title is ", resp.choices[0].message.content)

    return resp.choices[0].message.content


# function to get conversation history
# @router.post("/store-conversation")
async def get_conversation(messages: ChatHistory):
    message_history = []
    # adds each message to the message history, when correct role (user or assistant)
    for message in messages.chat_messages:
        if message.role in __allowed_roles:
            message_history.append({
                "role": message.role,
                "content": message.content
            })
        else:
            # http exception because invalid role being sent should result in 404 error
            raise HTTPException(status_code=404, detail="Invalid role sent")
    print("History:", message_history)
    return message_history


async def store_conversation(message_history: list):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            for message in message_history:
                await cur.execute(
                    "INSERT INTO conversation_messages (role, content) VALUES (%s, %s)",
                    (message['role'], message['content'])
                )


@router.post("/store-conversation")
async def handle_store_conversation(messages: ChatHistory):
    message_history = await get_conversation(messages)
    await store_conversation(message_history)
    message_history_title = await create_conversation_title(message_history)
    # return JSONResponse(content={"message": "Conversation stored successfully"})
    return Response(content=message_history_title, media_type='application/json')
