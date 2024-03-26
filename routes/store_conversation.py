import json
import os
from typing import Annotated, Union, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, Depends
from openai import AsyncOpenAI
from psycopg.rows import dict_row
from pydantic import BaseModel

from routes.authentication import AuthenticatedUser, get_current_user
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


class ConversationTitle(BaseModel):
    conversation_title: str


async def create_conversation_title(message_history: list[dict]) -> str:
    messages = message_history.copy()

    # adds question prompt to ask for suggestions
    messages.append({
        "role": "user",
        "content": "Based on the conversation so far, what is a title to summarise this conversation? "  # noqa
                   "Make sure to format in a JSON object with an array in the key 'title'."  # noqa
    })

    # gets response after asking openapi question
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=messages,
        response_format={
            "type": "json_object"
        }
    )

    # value was returning ["title"] so added [0] to get the string value instead
    title_string = json.loads(resp.choices[0].message.content)["title"][0]

    # return json.loads(resp.choices[0].message.content)["title"]
    return title_string


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


# async def store_conversation(message_history: list, conversation_title: str, username: str):
#     async with pool.connection() as conn:
#         async with conn.cursor() as cur:
#             await cur.execute(
#                 "INSERT INTO conversations (title, username)"
#                 " VALUES (%s, %s)",
#                 (conversation_title[100:], username),
#             )
#             for idx, message in message_history:
#                 await cur.execute(
#                     "INSERT INTO messages (role, content, idx) VALUES (%s, %s, %s)",
#                     (message['role'], message['content'])
#                 )
#
#
# @router.post("/store_conversation")
# async def handle_store_conversation(messages: ChatHistory,
#                                     user: AuthenticatedUser =
#                                     Depends(get_current_user)):
#     username = user.username
#     message_history = await get_conversation(messages)
#     message_history_title = await create_conversation_title(message_history)
#     await store_conversation(message_history, message_history_title, username)
#     # await store_conversation_title(message_history_title, username)
#     # return JSONResponse(content={"message": "Conversation stored successfully"})
#     return Response(content=message_history_title, media_type='application/json')


class Conversation(BaseModel):
    id: UUID
    title: str


# Loads conversations on left side
@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(current_user: Annotated[
    Union[AuthenticatedUser],
    Depends(get_current_user)
]):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT id, title FROM conversations WHERE username = %s", (current_user.username,))
            conversations = await cur.fetchall()

            return conversations


@router.get("/conversations/{conversation_id}", response_model=List[ConversationMessage])
async def get_conversation_history(conversation_id: UUID, current_user: Annotated[
    Union[AuthenticatedUser],
    Depends(get_current_user)
]):
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # Check if the user and conversation id match from db
            await cur.execute("SELECT 1 FROM conversations WHERE username = %s AND id = %s",
                              (current_user.username, conversation_id))

            if cur.fetchone() is None:
                raise HTTPException(status_code=403, detail="You don't have access to this conversation")

            # Fetch the message content, role and order by conversation_history(idx)
            # and return a dict for converting to List[ConversationMessage]
            await cur.execute("SELECT messages.content, messages.role FROM conversation_history "
                              "JOIN messages ON message_id = id "
                              "WHERE conversation_id = %s ORDER BY conversation_history.idx", (conversation_id,))

            history = await cur.fetchall()

            return history


# Creating a new conversation when the user click on the "new chat" button
@router.post("/conversations/create")
async def create_conversation(current_user: Annotated[
    Union[AuthenticatedUser],
    Depends(get_current_user)
]):
    username = current_user.username
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Insert a new conversation into the conversations table
            await cur.execute("INSERT INTO conversations (username) VALUES (%s) RETURNING id",
                              (username,))
            conversation_id = await cur.fetchone()
            return {"conversation_id": conversation_id}


# After every message
@router.post("/conversations/{conversation_id}/add_messages")
async def add_messages(new_messages: List[ConversationMessage],
                       conversation_id: UUID,
                       current_user: Annotated[
                           Union[AuthenticatedUser],
                           Depends(get_current_user)
                       ]):

    order_in_convo = 0
    # for each new message from assistant and user
    for message in new_messages:
        # print(message.role)
        # print(message.content)

        # insert into messages table and then conversation_history table
        # currently doesn't work? error: insert or update on tabel messages violates foreign key constraint fk_messages_conversation_history
        # key id not present in table conversation history
        async with pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO messages (role, content) VALUES (%s, %s) RETURNING id",
                                      (message.role, message.content,))
                    message_id = await cur.fetchone()

                    await cur.execute(
                        "INSERT INTO conversation_history (conversation_id, message_id, idx) VALUES (%s, %s, %s)",
                        (conversation_id, message_id, order_in_convo,))

        # the two insert statements separately
        # async with pool.connection() as conn:
        #     async with conn.cursor() as cur:
        #         await cur.execute("INSERT INTO conversation_history (conversation_id, message_id, idx) VALUES (%s, %s, %s)",
        #                           (conversation_id, message_id, order_in_convo,))

        # async with pool.connection() as conn:
        #     async with conn.cursor() as cur:
        #         await cur.execute(query, (message.role, message.content, conversation_id, order_in_convo,))

        # increment for next message in conversation
        order_in_convo += 1

    # Fetch the max idx for the conversation from the conversation_history table
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT MAX(idx) FROM conversation_history WHERE conversation_id = %s",
                            (conversation_id,))

            max_idx_dict = await cur.fetchone()

            if cur.fetchone() is None:
                # if no max idx found, assume its 1
                max_idx = 1
            else:
                max_idx = max_idx_dict['max']

    # If it's the first set of messages, generate a title and update the conversation
    # max idx is 2 when the user and assistant has responded once each,
    # so first set of messages is 2 but could be 1, so use < 3?
    if max_idx < 3:
        # generates conversation title
        conversation_title = await create_conversation_title(new_messages)

        # updates current value of title to the new title
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE conversations SET title = %s WHERE id = %s AND username = %s",
                    (conversation_title, conversation_id, current_user.username))

        return Response(
            content={"message": "Title updated, and inserted messages into tables"},
            media_type='application/json')

    else:
        return Response(
            content={"message": "Title not updated, but inserted messages into tables"},
            media_type='application/json')


# Delete the whole conversation from the database
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID, current_user: Annotated[
    Union[AuthenticatedUser],
    Depends(get_current_user)
]):
    username = current_user.username
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Check if the user own the conversation
            await cur.execute("SELECT username FROM conversations WHERE id = %s", (conversation_id,))
            conversation_owner = await cur.fetchone()
            if conversation_owner is None or conversation_owner[0] != username:
                raise HTTPException(status_code=403, detail="You don't have permission to delete this conversation")
            # Delete the records from the conversation_history table first since it contains foreign keys
            await cur.execute("DELETE FROM conversations WHERE id = %s",
                              (conversation_id, ))
            return {"message": "Conversation deleted"}
