import os
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Response, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

from utils.models import ConversationMessage

router = APIRouter()

# use api key to allow usage of together AI
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )

__allowed_roles = ["user", "assistant"]


# used to get correct format of list from frontend
class ChatHistory(BaseModel):
    chat_messages: list[ConversationMessage]


# get conversation from the UI
async def get_conversation(convo_history: list[dict]):
    # new variable to avoid continuously appending to input_messages
    previous_messages = convo_history.copy()

    # return the messages
    print("Message:", previous_messages)
    return previous_messages


# function to get conversation history
@router.post("/store-conversation")
async def store_conversation(messages: ChatHistory):
    # sets default start of the conversation history, with specific role 'system'
    message_history = [
        {
            "role": "system",
            "content": "You're an assistant that helps university students at Cardiff University. " # noqa
            "You can help me by answering my questions."
        }
    ]

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

    # gets conversation messages as json array
    conversation_history = await get_conversation(message_history)
    print("History:", conversation_history)
    return JSONResponse(content=conversation_history)
