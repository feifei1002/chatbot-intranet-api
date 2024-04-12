from pydantic import BaseModel


class ConversationMessage(BaseModel):
    """
    A message in a conversation
    """
    role: str
    content: str
