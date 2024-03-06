import os

from fastapi import APIRouter, Response
from openai import AsyncOpenAI
from pydantic import BaseModel
from datetime import date

from routes.chat import ConversationMessage

router = APIRouter()

# use api key to allow usage of openai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )

__allowed_roles = ["user", "assistant"]

storage = {}


class ChatHistory(BaseModel):
    chat_messages: list[ConversationMessage]


# uses api to suggest 3 questions based on the previous chat history
async def get_three_questions(suggest, convo_history):
    # new variable to avoid continuously appending to input_messages
    previous_messages = convo_history

    # adds question prompt to ask for suggestions
    previous_messages.append(
        {"role": "user", "content": str(suggest)})

    # gets response after asking openapi question
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=previous_messages,
        response_format={
            "type": "json_object"
        }
    )

    # return response from api
    return str(resp.choices[0].message.content)


@router.post("/chat_history")
async def get_chat_history(messages: ChatHistory):
    message_history = [
        {
            "role": "system",
            "content": "You're an assistant that helps university students at Cardiff University."  # noqa
                       " You can help me by answering my questions."
                       " You can also ask me questions."
                       f"\nCurrent Date: {date.today()}"
        }
    ]

    for message in messages.chat_messages:
        if message.role not in __allowed_roles:
            raise ValueError(f"Role {message.role} is not allowed")

        message_history.append(message.model_dump())

    # print("history is ", message_history)

    storage['history'] = message_history

    return message_history


# function to ask question to openai and get response
@router.get("/suggested")
async def suggested_questions():
    # gets history of questions

    if 'history' not in storage:
        return Response(status_code=200)

    history = storage['history']

    # history = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    # ]

    print(history)

    if history:
        # gets 3 suggested questions as json array
        suggested_qs = await get_three_questions(
            "Based on this conversation history, "
            "what are 3 good questions to ask after this conversation? "
            "Make sure to format in a JSON object with an array "
            "in the key 'questions'.",
            history)

        # print(suggested_qs)

        # sends JSON response of the questions
        return Response(content=suggested_qs, media_type='application/json')
    else:
        # if no chat history, respond with only status code and no json
        return Response(status_code=200)
