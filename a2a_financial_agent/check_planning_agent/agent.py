import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

def check_planned_expense(department: str, amount: float, supplier: str) -> str:
    """
    Verifica se uma despesa está planejada no orçamento.

    Args:
        department: O departamento da despesa
        amount: O valor da despesa
        supplier: O fornecedor

    Returns:
        Uma string indicando se a despesa foi planejada ou não
    """
    try:
        expenses_file = Path(__file__).parent.parent / "database" / "expenses.csv"
        df = pd.read_csv(expenses_file)
        
        # Converte o valor para float para comparação
        df['amount'] = df['amount'].astype(float)
        
        print(f"Valores a serem verificados: {department}, {amount}, {supplier}")
        
        matching_expense = df[
            (df['department'].str.lower() == department.lower()) &
            (df['amount'] == amount) &
            (df['supplier'].str.lower() == supplier.lower())
        ]
        
        if not matching_expense.empty:
            return "Despesa foi planejada"
        else:
            return "Despesa não foi planejada"

    except Exception as e:
        print(f"Erro ao verificar despesa planejada: {e}")
        return "Despesa não foi planejada"


def create_agent() -> LlmAgent:
    """Constrói o agente ADK para verificação de despesas planejadas."""
    return LlmAgent(
        model=LiteLlm("openai/gpt-4.1-nano"),
        name="check_planning_agent",
        instruction="""
            **Papel:** Você é um agente especializado em verificar se despesas estão planejadas no orçamento.
            Sua única responsabilidade é verificar se uma despesa específica (valor, departamento e fornecedor) está planejada.

            **Diretrizes Principais:**

            * **Verificação de Planejamento:** Use a ferramenta `check_planned_expense` para verificar se a despesa está planejada.
                A ferramenta requer três parâmetros:
                - `department`: O departamento da despesa
                - `amount`: O valor da despesa
                - `supplier`: O fornecedor
            * **Respostas Claras:** Sempre responda de forma clara e direta.
            * **Foco no Papel:** Não se envolva em conversas fora do contexto de verificação de planejamento.
                Se perguntado sobre outros assuntos, educadamente diga que só pode ajudar com verificações de planejamento.
        """,
        tools=[check_planned_expense],
    )