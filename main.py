from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils import suggested_questions

app = FastAPI()
app.include_router(suggested_questions.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}
