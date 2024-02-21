import os

from fastapi import APIRouter
from openai import AsyncOpenAI

router = APIRouter()

# use api key to allow usage of openai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                base_url='https://api.together.xyz',)

# specifically set question to start with
first_question = """What is the breed of the largest cat?"""

# data sent to openai
input_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

# temporarily stores conversations history
chat_history = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": first_question},
        ]

# function to ask question to openai and get response
@router.get("/utils/test")
async def suggestions_test():
    input_messages.append({"role": "user", "content": first_question})
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=input_messages
    )
    # adds to chat history
    chat_history.append({"role": "assistant", "content": (resp.choices[0].message.content)})
    print(chat_history)
    # sends response to page
    return {"message": resp.choices[0].message.content}