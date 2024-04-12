from typing import List, Union

from openai import BaseModel

from utils.learning_central_helper import get_cached_cookies, \
    extract_learning_central_stream_entries, \
    LearningCentralStreamEntry, GradeDetails


class StreamEntriesResponse(BaseModel):
    """
    A response containing the stream entries
    """
    stream_entries: List[Union[LearningCentralStreamEntry, GradeDetails]]


async def get_learning_central_stream(username: str, cookies_dict: dict) -> str:
    # Get the cookies for learning central
    cookies = await get_cached_cookies(username, cookies_dict)

    # Extract the stream entries using the cookies
    stream_entries = await extract_learning_central_stream_entries(cookies)

    return StreamEntriesResponse(stream_entries=stream_entries).model_dump_json()
