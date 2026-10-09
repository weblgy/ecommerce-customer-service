from atguigu.domain.message import UserMessage, ProcessResult
from atguigu.domain.state import DialogueState
from atguigu.engine.dialogue_engine import dialogue_engine
from atguigu.repository.dialogue_state_repository import DialogueStateRepository


class DialogueService:

    def __init__(self,dialogue_state_repository:DialogueStateRepository):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine=dialogue_engine

    async def process_message(self,user_message:UserMessage) -> ProcessResult:
        # 根据sender_id获取对话状态
        state:DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)
        #将对话状态和最新消息交给DialogueEngine处理
        process_result:ProcessResult = await self.dialogue_engine.process_message(state,user_message)
        #保存最新的对话状态
        await self.dialogue_state_repository.save_state(state)
        #返回处理结果
        return process_result