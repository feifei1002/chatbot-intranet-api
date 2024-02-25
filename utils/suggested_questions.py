import os

from fastapi import APIRouter, Response
from openai import AsyncOpenAI
import json

router = APIRouter()

# use api key to allow usage of openai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )


# function to create a basic conversation, so it can be used for suggestions
async def placeholder_conversation():
    # specifically set question for testing,
    # delete once chatbot conversations are implemented
    first_question = "What is Cardiff University known for?"

    # current history of the conversation with the chatbot
    input_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": first_question}
    ]

    # test conversation with api,
    # when working conversation with chatbot functions,
    # replace input_messages with full conversation
    try:
        api_response = await client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=input_messages
        )
        # add response to end of conversation history
        input_messages.append(
            {"role": "assistant", "content":
                str(api_response.choices[0].message.content)})
    except Exception:
        # when failure to get conversation response
        print("Error getting response from api: ", Exception)

    return input_messages


# uses api to suggest 3 questions based on the previous chat history
async def get_three_questions(suggest, convo_history):
    # new variable to avoid continuously appending to input_messages
    previous_messages = convo_history

    try:
        # adds question prompt to ask for suggestions
        previous_messages.append(
            {"role": "user", "content": str(suggest)})

        # gets response after asking openapi question
        resp = await client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=previous_messages
        )

        # only return response from api if succeeds
        return str(resp.choices[0].message.content)
    except Exception:
        # when failure to get conversation response
        print("Error getting response from api: ", Exception)


# function to ask question to openai and get response
@router.get("/suggested")
async def suggested_questions():
    try:
        # gets history of questions
        history = await placeholder_conversation()
        # gets 3 suggested questions as json array
        suggested_qs = await get_three_questions(
            "Based on this conversation history, "
            "what are 3 good questions to ask after this conversation? "
            "But output the 3 questions as 3 elements in JSON format.",
            history)
        # makes sure file format is correct
        json_suggested_qs = json.dumps(suggested_qs, default=str)

        # sends JSON response of the questions
        return Response(content=json_suggested_qs, media_type='application/json')
    except Exception:
        # when error with getting suggested questions
        print("Error getting suggested questions: ", Exception)
        # returns error code 500 because likely server side error
        return Response("Internal server error", status_code=500)
