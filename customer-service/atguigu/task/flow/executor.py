from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.flow.links import FlowStepLink, ConditionalLink, FallbackLink
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.flow.steps import FlowStep, StartFlowStep, CollectSlotStep, ActionFlowStep, ResponseFlowStep, \
    EndFlowStep


class FlowExecutor:
    def __init__(self,max_steps_per_turn: int = 100) -> None:
        self.max_steps_per_turn = max_steps_per_turn

    def run_task(self,state:DialogueState,flows:FlowCatalog,user_message:UserMessage) -> list[BotMessage]:
        if not state.task_state.active:
            return []

        flow:Flow = flows.get_flow_by_id(state.task_state.active.flow_id)
        step:FlowStep = flow.get_step_by_id(state.task_state.active.step_id)

        for _ in range(self.max_steps_per_turn):
            if isinstance(step,StartFlowStep):
                self.advance(step,state)
                continue

            if isinstance(step,CollectSlotStep):
                pass

            if isinstance(step,ActionFlowStep):
                pass

            if isinstance(step,ResponseFlowStep):
                pass

            if isinstance(step,EndFlowStep):
                pass

    def advance(self, step:FlowStep, state:DialogueState):
        next_step_id = self._select_next_step(step.next, state)
        state.task_state.active.step_id = next_step_id

    def _select_next_step(self, next:list[FlowStepLink], state:DialogueState) -> str:
        if len(next) == 1:
            return next[0].target
        for link in next:
            if isinstance(link,ConditionalLink):
                # 校验condition是否成立
                result = bool(eval(link.condition,{'__builtins__':{}},{'slots':state.task_state.active.slots}))
                # 成立：return target
                if result:
                    return link.target
                # 不成立：continue
                continue
            if isinstance(link,FallbackLink):
                return link.target

            