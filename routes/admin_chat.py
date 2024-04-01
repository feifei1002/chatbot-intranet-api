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


@router.get("/admin_chat")
async def admin_chat():
    user_questions = await get_user_questions()

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
    <tools>{tool_description}</tools>
    """

    function_calling_message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[
            {"role": "user",
             "content": "What are the 10 most asked questions?"
             }],
        system=system_prompt
    ).content[0].text

    print(function_calling_message)
