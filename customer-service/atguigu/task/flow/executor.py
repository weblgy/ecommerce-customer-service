from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.flow.conditions import ConditionEvaluator
from atguigu.task.flow.links import FlowStepLink, ConditionalLink, FallbackLink
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.flow.steps import FlowStep, StartFlowStep, CollectSlotStep, ActionFlowStep, ResponseFlowStep, \
    EndFlowStep
from atguigu.task.response.renderer import ResponseRenderer


class FlowExecutor:
    def __init__(
        self,
        condition_evaluator: ConditionEvaluator,
        response_renderer: ResponseRenderer,
        max_steps_per_turn: int = 100
    ) -> None:
        self.response_renderer = response_renderer
        self.condition_evaluator = condition_evaluator
        self.max_steps_per_turn = max_steps_per_turn

    def run_task(self,state:DialogueState,flows:FlowCatalog,user_message:UserMessage) -> list[BotMessage]:
        bot_message: list[BotMessage] = []
        if not state.task_state.active:
            return bot_message

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
                bot_message = self.response_renderer.render(step.template, state, user_message)
                bot_message.append(bot_message)
                self.advance(step,state)
                continue

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
                result = self.condition_evaluator.evaluate(link.condition, {'slots': state.task_state.active.slots})
                # 成立：return target
                if result:
                    return link.target
                # 不成立：continue
                continue
            if isinstance(link,FallbackLink):
                return link.target

            