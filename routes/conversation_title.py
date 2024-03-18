import os

from fastapi import APIRouter, Response
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


# function to create a title based on the conversation history,
# used to store previous conversations on the left pane of the chatbot page
@router.get("/conversation_title")
async def create_title_from_conversation():
    # test conversation to check title creation works
    message_history = [
        {"role": "user",
         "content": "How old is cardiff univeristy?"},
        {"role": "assistant",
         "content": "Established in 1883."},
        {"role": "user",
         "content": "How old is birmingham univeristy?"},
        {"role": "assistant",
         "content": "Established in 1825."}
    ]

    # # adds each message to the message history, when correct role (user or assistant)
    # for message in messages.chat_messages:
    #     if message.role in __allowed_roles:
    #         message_history.append({
    #             "role": message.role,
    #             "content": message.content
    #         })
    #     else:
    #         http exception because invalid role being sent should result in 404 error
    #         raise HTTPException(status_code=404, detail="Invalid role sent")

    # adds question prompt to ask for suggestions
    message_history.append(
        {"role": "user",
         "content": "Based on the conversation so far, what is a title to summarise this conversation? "  # noqa
                    "Make sure to format in a JSON object with an array in the key 'title'."})  # noqa

    # gets response after asking openapi question
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=message_history,
        response_format={
            "type": "json_object"
        }
    )

    return Response(content=resp.choices[0].message.content, media_type='application/json')
