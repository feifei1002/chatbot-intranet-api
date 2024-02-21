import os

from fastapi import APIRouter, Response
from openai import AsyncOpenAI
import json

router = APIRouter()

# use api key to allow usage of openai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )

# specifically set question to start with
first_question = "What is the breed of the largest cat?"

# data sent to openai
input_messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": first_question}
]


# function to ask question to openai and get response
@router.get("/suggested")
async def suggested_questions():
    # test conversation to check the api can review this
    # conversation and create suggested qs from it
    await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=input_messages
    )

    # gets 3 suggested questions as json array
    suggested_qs = await json_suggestions(
        "In only the format of a JSON array, "
        "what are 3 good questions to ask after this conversation?"
        "but do not explain reasoning for each question.")
    # makes sure file format is correct
    json_suggested_qs = json.dumps(suggested_qs, default=str)

    # sends response to page
    return Response(content=json_suggested_qs, media_type='application/json')


async def json_suggestions(suggest):
    # potential issue with continuous appending to list of dictionaries
    previous_messages = input_messages
    previous_messages.append(
        {"role": "user", "content": suggest})

    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=previous_messages
    )
    return resp.choices[0].message.content
