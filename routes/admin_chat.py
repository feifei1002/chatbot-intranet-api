import os
import re

from utils.db import pool
from fastapi import APIRouter
import anthropic

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def get_user_questions(user_questions):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT content FROM messages WHERE role = 'user'"
            )
            result = await cur.fetchall()
            return result


tool_description = f"""
<tool_description>
    <tool_name>get_user_questions</tool_name>
    <description>
        Function for getting all the questions asked by users.  
    <parameters>
        <parameter>
            <name>user_questions</name>
            <type>str</type>
            <description>Questions asked by users</description>
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


async def admin_chat(question):
    function_calling_message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[question],
        system=system_prompt,
    ).content[0].text
    function_params = {"user_questions": extract_between_tags("user_questions", function_calling_message)[0]}
    function_name = extract_between_tags("tool_name", function_calling_message)[0]
    names_to_functions = {'get_user_questions': get_user_questions}
    answer = await names_to_functions[function_name](**function_params)
    function_results = f"""
        <function_results>
          <result>
            <tool_name>get_stock_price</tool_name>
            <stdout>{answer}</stdout>
          </result>
        </function_results>"""
    partial_assistant_message = function_calling_message + function_results
    final_message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[question,
                  {
                      "role": "assistant",
                      "content": partial_assistant_message
                  }
                  ],
        system=system_prompt,
    ).content[0].text
    print("\n\n##### After Function Calling #####" + final_message)
    return final_message


def extract_between_tags(tag, string, strip=False):
    ext_list = re.findall(f"<{tag}>(.*?)</{tag}>", string, re.DOTALL)
    return [e.strip() for e in ext_list] if strip else ext_list


@router.get("/10_most_asked_questions")
async def get_10_most_asked_questions():
    question = {
        "role": "user",
        "content": "What are the 10 most asked questions in general?"
    }
    response = await admin_chat(question)
    return response


@router.get("/5_most_asked_questions_uni_website")
async def get_5_most_asked_questions_uni_website():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions related to the University's website?"
    }
    response = await admin_chat(question)
    return response


@router.get("/5_most_asked_questions_student_life")
async def get_5_most_asked_questions_intranet():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions related to the student life?"
    }
    response = await admin_chat(question)
    return response
