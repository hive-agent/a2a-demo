import asyncio
import json
import logging
import uuid
from typing import Any, AsyncIterable, List
from google.adk.models.lite_llm import LiteLlm

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TextPart,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from openai.types.chat import ChatCompletionMessage

from .remote_connection import RemoteAgentConnections

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Carrega variáveis de ambiente e configura o asyncio
load_dotenv()
nest_asyncio.apply()

# Configuração dos agentes remotos
REMOTE_AGENTS = [
    "http://localhost:10002",  # check_budget_agent
    "http://localhost:10003",  # check_planning_agent
    "http://localhost:10004",  # check_legal_agent
]


class FinancialOrchestratorAgent:
    """O agente orquestrador financeiro."""

    def __init__(self):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self._agent = self.create_agent()
        self._user_id = "finance_orchestrator"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _async_init_components(self, remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(f"ERROR: Failed to get agent card from {address}: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to initialize connection for {address}: {e}")

        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("agent_info:", agent_info)
        self.agents = "\n".join(agent_info) if agent_info else "No agents found"

    @classmethod
    async def create(cls, remote_agent_addresses: List[str]):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model=LiteLlm("openai/gpt-4.1-nano"),
            name="financial_orchestrator",
            instruction=self.root_instruction,
            description="Agente que coordena verificações de despesas com agentes especializados.",
            tools=[self.send_message],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
        **Papel:** Você é o Agente Orquestrador Financeiro, responsável por coordenar a aprovação de despesas de negócios.

        **Diretrizes Principais:**

        * **Coordenação de Verificações:**
            * Use APENAS os agentes que estão disponíveis na lista abaixo
            * Se um agente não estiver disponível, NÃO tente chamá-lo
            * Use o agente de check_budget_agent (se disponível) para verificar se há dinheiro disponível
            * Use o agente de check_planning_agent (se disponível) para verificar se a despesa está no orçamento
            * Use o agente de check_legal_agent (se disponível) para verificar contratos com fornecedores

        * **Processo de Decisão:**
            * Use APENAS os agentes que estão disponíveis
            * Considere todas as verificações possíveis com os agentes disponíveis
            * Documente claramente o motivo da decisão
            * Deixe claro quais agentes foram usados e quais não estavam disponíveis

        * **Comunicação:**
            * Mantenha o usuário informado sobre o progresso das verificações
            * Apresente as respostas de cada agente de forma clara
            * Forneça uma justificativa detalhada para a decisão final

        * **Formato da Resposta:**
            * Use marcadores para melhor legibilidade
            * Inclua o status de cada verificação realizada
            * Apresente a decisão final claramente (✅ Aprovado ou ❌ Rejeitado)
            * Uma decisão só pode ser aprovada se todos os agentes disponíveis aprovarem a despesa

        <Agentes Disponíveis>
        {self.agents}
        </Agentes Disponíveis>

        IMPORTANTE: Use APENAS os agentes listados acima. Se um agente não estiver na lista, ele não está disponível e não deve ser chamado.
        """

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        """Streams a resposta do agente para uma consulta."""
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = ChatCompletionMessage(role="user", content=query)
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if event.content and event.content.parts and event.content.parts[0].text:
                    response = "\n".join([p.text for p in event.content.parts if p.text])
                yield {"is_task_complete": True, "content": response}
            else:
                yield {"is_task_complete": False, "updates": "O agente financeiro está pensando..."}

    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        """Envia uma tarefa para um agente remoto."""
        if agent_name not in self.remote_agent_connections:
            logger.warning(f"Tentativa de chamar agente não disponível: {agent_name}")
            return [{"text": f"Agente {agent_name} não está disponível no momento."}]

        client = self.remote_agent_connections[agent_name]

        if not client:
            logger.warning(f"Cliente não disponível para {agent_name}")
            return [{"text": f"Cliente não disponível para {agent_name}"}]

        # Gerenciamento simplificado de task e context ID
        state = tool_context.state
        task_id = state.get("task_id", str(uuid.uuid4()))
        context_id = state.get("context_id", str(uuid.uuid4()))
        message_id = str(uuid.uuid4())

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            },
        }

        try:
            message_request = SendMessageRequest(
                id=message_id, params=MessageSendParams.model_validate(payload)
            )
            send_response: SendMessageResponse = await client.send_message(message_request)
            logger.debug("send_response %s", send_response)

            if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(
                send_response.root.result, Task
            ):
                logger.warning("Recebida uma resposta não-sucedida ou não-task")
                return [{"text": f"Erro ao chamar agente {agent_name}"}]

            response_content = send_response.root.model_dump_json(exclude_none=True)
            json_content = json.loads(response_content)

            resp = []
            if json_content.get("result", {}).get("artifacts"):
                for artifact in json_content["result"]["artifacts"]:
                    if artifact.get("parts"):
                        resp.extend(artifact["parts"])
            return resp
        except Exception as e:
            logger.error(f"Erro ao chamar agente {agent_name}: {str(e)}")
            return [{"text": f"Erro ao chamar agente {agent_name}: {str(e)}"}]


def _get_initialized_financial_agent_sync():
    """Sincronamente cria e inicializa o FinancialOrchestratorAgent."""

    async def _async_main():
        print("inicializando agente financeiro")
        financial_agent_instance = await FinancialOrchestratorAgent.create(
            remote_agent_addresses=REMOTE_AGENTS
        )
        print("FinancialOrchestratorAgent inicializado")
        return financial_agent_instance.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Aviso: Não foi possível inicializar FinancialOrchestratorAgent com asyncio.run(): {e}. "
                "Isso pode acontecer se um event loop já estiver rodando (ex: em Jupyter). "
                "Considere inicializar FinancialOrchestratorAgent dentro de uma função async em sua aplicação."
            )
        else:
            raise


root_agent = _get_initialized_financial_agent_sync()
