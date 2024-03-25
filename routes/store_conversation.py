import json
import os
import re

import numpy as np
from fastapi import APIRouter, HTTPException, Response, Depends
from openai import AsyncOpenAI
from pydantic import BaseModel
import psycopg

from routes.authentication import AuthenticatedUser, get_current_user_optional
from utils.db import pool
from utils.models import ConversationMessage

router = APIRouter()

# use api key to allow usage of TogetherAI
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                     base_url='https://api.together.xyz', )

__allowed_roles = ["user", "assistant"]


async def get_authenticated_user():
    username = AuthenticatedUser.username
    return username


class ChatHistory(BaseModel):
    chat_messages: list[ConversationMessage]

class ConversationTitle(BaseModel):
    conversation_title: str


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

    # print("title is ", resp.choices[0].message.content)

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
    # print("History:", message_history)
    # print("User:", messages.user.username)
    return message_history


# store role and content into conversation_messages database
# async def store_conversation(message_history: list):
#     async with pool.connection() as conn:
#         async with conn.cursor() as cur:
#             for message in message_history:
#                 await cur.execute(
#                     "INSERT INTO conversation_messages (role, content) VALUES (%s, %s)",
#                     (message['role'], message['content'])
#                 )

async def store_conversation(message_history: list, conversation_title: str, username: str):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO conversations (conversation_title, username)"
                " VALUES (%s, %s)",
                # Only extract the title, remove everything before index 21
                # and the last 7 indices of the title
                (conversation_title[21:-7], username),
            )
            for message in message_history:
                await cur.execute(
                    "INSERT INTO conversation_messages (role, content) VALUES (%s, %s)",
                    (message['role'], message['content'])
                )


# store conversation title and username into conversations database
# async def store_conversation_title(conversation_title: str, username: str):
#     async with pool.connection() as conn:
#         async with conn.cursor() as cur:
#             await cur.execute(
#                 "INSERT INTO conversations (conversation_id, conversation_title, username)"
#                 " VALUES (gen_random_uuid (), %s, %s)",
#                 # Only extract the title, remove everything before index 21
#                 # and the last 7 indices of the title
#                 (conversation_title[21:-7], username),
#             )


# get conversation id for given title and username from database
async def get_conversation_id(conversation_title: str, username: str):
    conn = await pool.getconn()
    try:
        async with conn.cursor() as cursor:
            query = "SELECT conversation_id FROM conversations WHERE conversation_title = %s AND username = %s"
            await cursor.execute(query, (conversation_title,username))
            rows = await cursor.fetchall()

            # for row in rows:
            #     print(row)

            # return conversation id
            conversation_id = int(re.sub(r'[^\w]', ' ', str(rows[0])))
            # print("id is: ", conversation_id)

            return conversation_id
    except psycopg.Error as e:
        print("Error executing SELECT statement:", e)


# get message id from conversation id
async def get_message_id(conversation_id: int):
    conn = await pool.getconn()
    try:
        async with conn.cursor() as cursor:
            query = "SELECT message_id FROM conversation_history WHERE conversation_id = %s"
            await cursor.execute(query, (conversation_id,))
            rows = await cursor.fetchall()

            # return history message id
            # doesn't work yet because conversation_history is empty
            # message_id = int(rows[0])
            # print("message id is: ", rows)
            test_rows = (3,4)
            return test_rows
    except psycopg.Error as e:
        print("Error executing SELECT statement:", e)



# get role and content from message id
async def get_message_contents(message_id: list[int]):
    conn = await pool.getconn()
    try:
        rows = []
        async with conn.cursor() as cursor:
            for message in message_id:
                query = "SELECT role, content FROM conversation_messages WHERE message_id = %s"
                # conversation_history table empty so doesn't work yet
                await cursor.execute(query, (message,))
                rows.append(await cursor.fetchall())

            # for row in rows:
            #     print("role is: ", row[0][0])
            #     print("content is: ", row[0][1])

            # print(rows)
            conversation = [{t[0]: t[1]} for sublist in rows for t in sublist]
            print(conversation)
            return conversation
    except psycopg.Error as e:
        print("Error executing SELECT statement:", e)


@router.post("/store_conversation")
async def handle_store_conversation(messages: ChatHistory,
                                    user: AuthenticatedUser =
                                    Depends(get_current_user_optional)):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorised")
    username = user.username
    message_history = await get_conversation(messages)
    message_history_title = await create_conversation_title(message_history)
    await store_conversation(message_history, message_history_title, username)
    # await store_conversation_title(message_history_title, username)
    # return JSONResponse(content={"message": "Conversation stored successfully"})
    return Response(content=message_history_title, media_type='application/json')

@router.post("/get_conversation_from_title")
async def handle_send_conversation(title: ConversationTitle,
                                   user: AuthenticatedUser =
                                   Depends(get_current_user_optional)):
    username = user.username
    conversation_title = title.conversation_title

    # select values from databases using title and username
    conversation_id = await get_conversation_id(conversation_title, username)
    message_id = await get_message_id(conversation_id)
    conversation_history = await get_message_contents(message_id)

    # return conversation history
    return Response(content=json.dumps(conversation_history), media_type='application/json')
