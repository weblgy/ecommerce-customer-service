import uuid

from fastapi import APIRouter

from atguigu.app.schemas import ChatRequest, ChatResponse, ChatMessage, HistoryResponse, HistoryMessage

chat_router = APIRouter()


@chat_router.post("/api/chat")
async def chat(chat_request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        messages=[ChatMessage(text="Hello World!")]
    )


@chat_router.get("/api/chat/history")
async def getHistory(sender_id:str) -> HistoryResponse:
    return HistoryResponse(
        sender_id=sender_id,
        messages=[
            HistoryMessage(
                role="user",
                text="hi"
            ),
            HistoryMessage(
                role="bot",
                text="11"
            ),
        ]
    )