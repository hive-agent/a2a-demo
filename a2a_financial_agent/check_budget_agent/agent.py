import os
from pathlib import Path
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

def check_budget(value: float) -> str:
    """
    Verifica se há orçamento disponível para o valor solicitado.

    Args:
        value: O valor a ser verificado

    Returns:
        Uma string indicando se há orçamento disponível ou não
    """
    try:
        budget_file = Path(__file__).parent.parent / "database" / "current_budget.txt"
        with open(budget_file, "r") as f:
            current_budget = float(f.read().strip())

        if current_budget >= value:
            return "Tem budget disponível"
        else:
            return "Não tem budget disponível"

    except Exception as e:
        print(f"Erro ao verificar orçamento: {e}")
        return "Não tem budget disponível"


def create_agent() -> LlmAgent:
    """Constrói o agente ADK para verificação de orçamento."""
    return LlmAgent(
        model=LiteLlm("openai/gpt-4.1-nano"),
        name="check_budget_agent",
        instruction="""
            **Papel:** Você é um agente especializado em verificar disponibilidade de orçamento.
            Sua única responsabilidade é verificar se há dinheiro disponível para um valor solicitado.

            **Diretrizes Principais:**

            * **Verificação de Orçamento:** Use a ferramenta `check_budget` para verificar se há dinheiro disponível.
                A ferramenta requer um parâmetro `value` que é o valor a ser verificado.
            * **Respostas Claras:** Sempre responda de forma clara e direta.
            * **Foco no Papel:** Não se envolva em conversas fora do contexto de verificação de orçamento.
                Se perguntado sobre outros assuntos, educadamente diga que só pode ajudar com verificações de orçamento.
        """,
        tools=[check_budget],
    )