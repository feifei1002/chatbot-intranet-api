import os

from fastapi import APIRouter, Response
from openai import AsyncOpenAI
from routes import chat

router = APIRouter()

# use api key to allow usage of openai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )


# function to create a basic conversation, so it can be used for suggestions
# async def placeholder_conversation():
#     # specifically set question for testing,
#     # delete once chatbot conversations are implemented
#     first_question = "What is Cardiff University known for?"
#
#     # current history of the conversation with the chatbot
#     input_messages = [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": first_question}
#     ]
#
#     # test conversation with api,
#     # when working conversation with chatbot functions,
#     # replace input_messages with full conversation
#     api_response = await client.chat.completions.create(
#         model="mistralai/Mixtral-8x7B-Instruct-v0.1",
#         messages=input_messages
#     )
#
#     # add response to end of conversation history
#     input_messages.append(
#         {"role": "assistant", "content":
#             str(api_response.choices[0].message.content)})
#
#     return input_messages


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


# function to ask question to openai and get response
@router.get("/suggested")
async def suggested_questions():
    # gets history of questions

    # below line doesnt work
    history = chat.get_chat_history()
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
