import logging
from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BudgetAgentExecutor(AgentExecutor):
    """Um AgentExecutor que executa o agente de verificação de orçamento."""

    def __init__(self, runner: Runner):
        self.runner = runner
        self._running_sessions = {}

    def _run_agent(
        self, session_id, new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        return self.runner.run_async(
            session_id=session_id, user_id="check_budget_agent", new_message=new_message
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        session_obj = await self._upsert_session(session_id)
        session_id = session_obj.id

        try:
            async for event in self._run_agent(session_id, new_message):
                if event.is_final_response():
                    parts = convert_genai_parts_to_a2a(
                        event.content.parts if event.content and event.content.parts else []
                    )
                    logger.debug("Yielding final response: %s", parts)
                    await task_updater.add_artifact(parts)
                    await task_updater.complete()
                    break
                if not event.get_function_calls():
                    logger.debug("Yielding update response")
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            convert_genai_parts_to_a2a(
                                event.content.parts
                                if event.content and event.content.parts
                                else []
                            ),
                        ),
                    )
                else:
                    logger.debug("Skipping event")
        except Exception as e:
            logger.error("Error in _process_request: %s", str(e))
            await task_updater.update_status(
                TaskState.failed,
                message=task_updater.new_agent_message([Part(root=TextPart(text=f"Erro ao processar requisição: {str(e)}"))]),
            )
            await task_updater.complete()
            raise

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        try:
            # Converte a mensagem A2A para o formato do Google Gen AI
            message_content = convert_a2a_parts_to_genai(context.message.parts)
            logger.debug("Converting message parts to Gen AI format: %s", message_content)
            
            await self._process_request(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message_content)],
                ),
                context.context_id,
                updater,
            )
        except Exception as e:
            logger.error("Error processing request: %s", str(e))
            await updater.update_status(
                TaskState.failed,
                message=updater.new_agent_message([Part(root=TextPart(text=f"Erro ao processar requisição: {str(e)}"))]),
            )
            await updater.complete()
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id="check_budget_agent", session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="check_budget_agent",
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> str:
    """Convert a list of A2A Part types into a Gen AI message content."""
    text_parts = []
    for part in parts:
        if isinstance(part.root, TextPart):
            text_parts.append(part.root.text)
    return "\n".join(text_parts)


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert Gen AI message content into a list of A2A Part types."""
    a2a_parts = []
    for part in parts:
        if hasattr(part, 'text') and part.text:
            a2a_parts.append(Part(root=TextPart(text=part.text)))
    return a2a_parts