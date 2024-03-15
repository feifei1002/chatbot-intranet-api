import json
from datetime import date

from fastapi import APIRouter
from openai import AsyncOpenAI
from opentelemetry import trace
from opentelemetry.trace import StatusCode  # Import StatusCode
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from utils import intranet_search_tool, uni_website_search_tool
from utils.models import ConversationMessage

router = APIRouter()


class ChatRequest(BaseModel):
    """
    A request to the chat endpoint
    """
    previous_messages: list[ConversationMessage]
    question: str


__allowed_roles = ["user", "assistant"]

client = AsyncOpenAI()


@router.post("/chat")
async def chat(chat_request: ChatRequest):
    chat_tracer = trace.get_tracer("chat_api")

    # Span for monitoring the overall processing time
    with chat_tracer.start_as_current_span("chat_processing") as span:
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You're an assistant that helps university students at Cardiff University."
                               " You can help me by answering my questions."
                               " You can also ask me questions."
                               "\nYou can use the following tools when a user asks a query: Intranet search, Search University Website"
                               "\nYou must use the responses from the tool to answer the student's query."
                               "\nWhen the user is asking a follow-up question, you need to use the previous messages to form the context of the new question for tools."
                               f"\nCurrent Date: {date.today()}"
                }
            ]

            # Check if the role for each message is allowed
            # this is to prevent the user from impersonating the system role function role, etc.
            for message in chat_request.previous_messages:
                if message.role not in __allowed_roles:
                    raise ValueError(f"Role {message.role} is not allowed")

                messages.append(message.model_dump())

            # Add the user's question to the messages
            messages.append({
                "role": "user",
                "content": chat_request.question
            })

            # Create the tools
            tools = [
                # Intranet tool
                {
                    "type": "function",
                    "function": {
                        "name": "search_intranet_documents",
                        "description": "Search the intranet's documents for a query, to help answer the user's query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The question to search for in the intranet's documents",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                },
                # University's website tool
                {
                    "type": "function",
                    "function": {
                        "name": "search_uni_website",
                        "description": "Search the Cardiff University website, to help answer the user's query",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The question to search for on Cardiff University's website",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }
            ]

            # Create an event generator to stream the response from OpenAI's format
            async def event_generator():
                # Init as true, so that the loop runs at least once
                function_call = True
                # Used for Together's format when streaming tokens
                # In OpenAI, this is set after the response is received
                function_call_content = ""

                async def inner_generator():
                    nonlocal function_call
                    nonlocal function_call_content

                    # Create a chat completion request
                    response = await client.chat.completions.create(
                        messages=messages,
                        model="gpt-3.5-turbo-0125",
                        stream=True,
                        tools=tools,
                        tool_choice="auto",
                    )

                    current_id = None
                    tool_calls_dict = {}

                    async for event in response:
                        choice = event.choices[0]
                        delta = choice.delta

                        # The assistant is trying to call a tool
                        if delta.tool_calls:
                            function_call = True

                            tool_call = delta.tool_calls[0]

                            # Start of a new tool call
                            if tool_call.id:
                                current_id = tool_call.id

                            # Set the name and arguments of the tool call
                            if tool_call.function.name:
                                tool_calls_dict[current_id] = {
                                    "name": tool_call.function.name,
                                    "arguments": ""
                                }
                            if tool_call.function.arguments:
                                tool_calls_dict[current_id]["arguments"] += tool_call.function.arguments
                        else:
                            # Stream back the assistant's message
                            content = delta.content
                            if content is not None:
                                yield json.dumps({
                                    "text": delta.content
                                })

                    if function_call and tool_calls_dict:
                        # Create OpenAI's format for tool_calls
                        tool_calls = []

                        # Used to convert the function call to string
                        # Like in Together's api
                        function_calls_list = []

                        # Parse our dictionary, and add it as an assistant message
                        # Also, convert to json for setting 'calls'
                        for key, value in tool_calls_dict.items():
                            tool_calls.append({
                                "id": key,
                                "type": "function",
                                "function": {
                                    "name": value["name"],
                                    "arguments": value["arguments"],
                                }
                            })

                            value["id"] = key
                            value["arguments"] = json.loads(value["arguments"])
                            function_calls_list.append(value)

                        # Add the assistant message to the messages
                        messages.append({
                            "content": None,
                            "role": "assistant",
                            "tool_calls": tool_calls,
                        })

                        function_call_content = json.dumps(function_calls_list)

                while function_call:
                    function_call = False
                    # We keep generating, until the assistant stops calling tools
                    with chat_tracer.start_as_current_span("completion_response") as span:
                        delta_count = 0
                        async for __event in inner_generator():
                            delta_count += 1
                            yield __event

                        span.set_attribute("delta_count", delta_count)
                        span.set_attribute("function_call", function_call)

                    if function_call:
                        calls = json.loads(function_call_content)
                        # Reset function call content,
                        # in case assistant wants to call functions again
                        function_call_content = ""

                        for call in calls:
                            name = call["name"]
                            match name:
                                case "search_intranet_documents":
                                    result = await intranet_search_tool \
                                        .search_intranet(**call["arguments"])
                                case "search_uni_website":
                                    result = await uni_website_search_tool \
                                        .search_uni_website(**call["arguments"])
                                case _:
                                    raise ValueError(
                                        f"Assistant called unknown function: {name}"
                                    )

                            # Add the function call as a message in the conversation
                            messages.append({
                                "tool_call_id": call.get("id"),
                                "role": "tool",
                                "name": name,
                                "content": result
                            })

            return EventSourceResponse(event_generator())

        except Exception as e:
            # Set status to indicate failure
            span.set_status(StatusCode.ERROR, str(e))
            raise  # Re-raise the exception for proper handling
