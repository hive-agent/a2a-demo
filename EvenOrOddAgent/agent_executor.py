from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from pydantic import BaseModel

class EvenOrOddAgent(BaseModel):
    """Agent that returns if a number is even or odd"""

    async def invoke(self, value: int) -> str:
        """Invoke the agent"""
        return "Even" if value % 2 == 0 else "Odd"
    

class EvenOrOddAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = EvenOrOddAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # Obtém o texto da mensagem do contexto
        message = context.message
        text_part = message.parts[0].root
        input_value = int(text_part.text)
        
        result = await self.agent.invoke(input_value)
        await event_queue.queue.put(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise NotImplementedError("Cancel is not implemented")
