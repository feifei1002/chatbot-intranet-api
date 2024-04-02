import os
from utils.db import pool
from fastapi import APIRouter
import anthropic

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def get_user_questions():
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT content FROM messages WHERE role = 'user'"
            )
            result = await cur.fetchall()
            return result


async def setup_tool_description(user_questions):
    tool_description = f"""
    <tool_description>
        <tool_name>get_user_questions</tool_name>
        <description>
            Function for getting all the questions asked by users.  
        <parameters>
            <parameter>
                f"{user_questions}"
            </parameter>
        </parameters>
    </tool_description>
    """
    return tool_description


async def setup_system_prompt(tool):
    system_prompt = f"""
    In this environment you have access to a set of tools you can use to generate analytics for the admin of a chatbot. 
    
    You may call them like this:
    <function_calls>
        <invoke>
            <tool_name>$TOOL_NAME</tool_name>
            <parameters>
                <$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>
                ...
            </parameters>
        </invoke>
    </function_calls>
    
    Here are the tools available:
    <tools>{tool}</tools>
    """

    return system_prompt


async def admin_chat(question):
    user_questions = await get_user_questions()
    tool = await setup_tool_description(user_questions)
    prompt = await setup_system_prompt(tool)

    function_calling_message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[question],
        system=prompt
    ).content[0].text
    print(function_calling_message)
    return function_calling_message


@router.get("/10_most_asked_questions")
async def get_10_most_asked_questions():
    question = {
        "role": "user",
        "content": "What are the 10 most asked questions in general?"
    }
    response = await admin_chat(question)
    print(response)
    return response


@router.get("/5_most_asked_questions_uni_website")
async def get_5_most_asked_questions_uni_website():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions related to the University's website?"
    }
    response = await admin_chat(question)
    print(response)
    return response


@router.get("/5_most_asked_questions_student_life")
async def get_5_most_asked_questions_intranet():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions related to the student life?"
    }
    response = await admin_chat(question)
    print(response)
    return response


