import os

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


# uses api to suggest 3 questions based on the previous chat history
async def get_three_questions(convo_history: list[dict]):
    # new variable to avoid continuously appending to input_messages
    previous_messages = convo_history.copy()

    # adds question prompt to ask for suggestions
    previous_messages.append(
        {"role": "user",
         "content": "Based on the conversation so far, what are 3 questions that you think I may be interested in asking next? " # noqa
            "Make sure to format in a JSON object with an array in the key 'questions'."}) # noqa

    # gets response after asking openapi question
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=previous_messages,
        response_format={
            "type": "json_object"
        }
    )

    # return response from api
    return resp.choices[0].message.content


# function to get conversation history and then suggestions three related questions
@router.post("/suggested")
async def suggest_questions_from_conversation(messages: ChatHistory):
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

    # gets 3 suggested questions as json array
    suggested_qs = await get_three_questions(message_history)

    # sends JSON response of the questions
    return Response(content=suggested_qs, media_type='application/json')
