import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List
from google.adk.models.lite_llm import LiteLlm

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver, A2AClient
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
from google.genai import types

# Carrega variáveis de ambiente e configura o asyncio
load_dotenv()
nest_asyncio.apply()


def create_agent(agents_info: str = "Nenhum agente configurado.") -> Agent:
    """
    Cria uma instância do agente com as configurações padrão.
    
    Args:
        agents_info: Informações sobre os agentes disponíveis
        
    Returns:
        Agent: Instância do agente configurado
    """
    return Agent(
        model=LiteLlm("openai/gpt-4.1-nano"),
        name="financial_orchestrator",
        instruction=f"""
        **Papel:** Você é o Agente Orquestrador Financeiro, responsável por coordenar a aprovação de despesas de negócios.

        **Diretrizes Principais:**

        * **Coordenação de Verificações:**
            * Use o agente de check_budget_agent para verificar se há dinheiro disponível
            * Use o agente de check_planning_agent para verificar se a despesa está no orçamento
            * Use o agente de check_legal_agent para verificar contratos com fornecedores

        * **Processo de Decisão:**
            * Aguarde as respostas de todos os agentes antes de tomar uma decisão
            * Considere todas as verificações ao aprovar ou rejeitar uma despesa
            * Documente claramente o motivo da decisão

        * **Comunicação:**
            * Mantenha o usuário informado sobre o progresso das verificações
            * Apresente as respostas de cada agente de forma clara
            * Forneça uma justificativa detalhada para a decisão final

        * **Formato da Resposta:**
            * Use marcadores para melhor legibilidade
            * Inclua o status de cada verificação
            * Apresente a decisão final claramente (✅ Aprovado ou ❌ Rejeitado)

        **Data Atual:** {datetime.now().strftime("%Y-%m-%d")}

        <Agentes Disponíveis>
        {agents_info}
        </Agentes Disponíveis>
        """,
        description="Agente que coordena verificações de despesas com agentes especializados.",
    )


class RemoteAgentConnections:
    """Classe para gerenciar conexões com agentes remotos."""
    
    def __init__(self, agent_card: AgentCard, agent_url: str):
        self.agent_card = agent_card
        self.agent_url = agent_url


class FinancialOrchestratorAgent:
    """
    Agente responsável por aprovar ou rejeitar despesas de negócios
    coordenando verificações com agentes especializados em orçamento,
    planejamento e aspectos legais.
    """

    def __init__(self):
        """Inicializa o agente financeiro."""
        self.remote_agent_connections = {}
        self.cards = {}
        self.agents = "Nenhum agente configurado."
        self._agent = create_agent(self.agents)
        self._user_id = "finance_orchestrator"
        self._runner = self._setup_runner()

    def _setup_runner(self) -> Runner:
        """Configura o runner do agente."""
        return Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def initialize(self, remote_agent_addresses: List[str]) -> None:
        """
        Inicializa as conexões com os agentes remotos.
        
        Args:
            remote_agent_addresses: Lista de endereços dos agentes remotos
        """
        if not remote_agent_addresses:
            print("Aviso: Nenhum agente remoto configurado. O agente funcionará em modo standalone.")
            return

        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                await self._initialize_remote_agent(client, address)

        self._update_agent_info()

    async def _initialize_remote_agent(self, client: httpx.AsyncClient, address: str) -> None:
        """Inicializa um agente remoto específico."""
        try:
            card_resolver = A2ACardResolver(client, address)
            card = await card_resolver.get_agent_card()
            
            remote_connection = RemoteAgentConnections(
                agent_card=card,
                agent_url=address
            )
            
            self.remote_agent_connections[card.name] = remote_connection
            self.cards[card.name] = card
            print(f"Agente conectado com sucesso: {card.name}")
            
        except Exception as e:
            print(f"AVISO: Não foi possível conectar ao agente em {address}: {e}")

    def _update_agent_info(self) -> None:
        """Atualiza as informações dos agentes disponíveis."""
        if not self.cards:
            return

        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        
        self.agents = "\n".join(agent_info)
        print("Agentes disponíveis:", self.agents)
        # Atualiza o agente com as novas informações
        self._agent = create_agent(self.agents)

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        """
        Processa uma consulta e retorna os resultados em stream.
        
        Args:
            query: A consulta a ser processada
            session_id: ID da sessão atual
            
        Yields:
            Dicionário com atualizações do processamento
        """
        session = await self._get_or_create_session(session_id)
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])

        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            yield self._process_event(event)

    async def _get_or_create_session(self, session_id: str) -> Any:
        """Obtém ou cria uma nova sessão."""
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        return session

    def _process_event(self, event: Any) -> dict[str, Any]:
        """Processa um evento do stream."""
        if event.is_final_response():
            response = ""
            if event.content and event.content.parts and event.content.parts[0].text:
                response = "\n".join([p.text for p in event.content.parts if p.text])
            return {"is_task_complete": True, "content": response}
        
        return {"is_task_complete": False, "updates": "O agente financeiro está pensando..."}


# Cria e exporta o agente raiz para o ADK
root_agent = create_agent()
