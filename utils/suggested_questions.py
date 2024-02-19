import os

from fastapi import APIRouter
from openai import AsyncOpenAI

router = APIRouter()

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

client = AsyncOpenAI(api_key=TOGETHER_API_KEY,
                base_url='https://api.together.xyz',
                )

# test input
test_input = """What is a large language model?"""


@router.get("/utils/test")
async def suggestions_test():
    resp = await client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": test_input
            }
        ]
    )

    return {"message": resp.choices[0].message.content}
