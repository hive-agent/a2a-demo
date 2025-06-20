import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

def check_legal_approval(department: str, amount: float, supplier: str) -> str:
    """
    Verifica se uma despesa foi aprovada pelo departamento jurídico.

    Args:
        department: O departamento da despesa
        amount: O valor da despesa
        supplier: O fornecedor

    Returns:
        Uma string indicando se a despesa foi aprovada pelo jurídico ou não
    """
    try:
        expenses_file = Path(__file__).parent.parent / "database" / "expenses.csv"
        df = pd.read_csv(expenses_file)
        
        # Converte o valor para float para comparação
        df['amount'] = df['amount'].astype(float)
        
        # Procura por uma despesa que corresponda aos critérios e tenha aprovação jurídica
        matching_expense = df[
            (df['department'].str.lower() == department.lower()) &
            (df['amount'] == amount) &
            (df['supplier'].str.lower() == supplier.lower()) &
            (df['approved_by_legal'].str.lower() == 'yes')
        ]
        
        if not matching_expense.empty:
            return "Aprovado pelo jurídico"
        else:
            return "Não aprovado pelo jurídico"

    except Exception as e:
        print(f"Erro ao verificar aprovação jurídica: {e}")
        return "Não aprovado pelo jurídico"


def create_agent() -> LlmAgent:
    """Constrói o agente ADK para verificação de aprovação jurídica."""
    return LlmAgent(
        model=LiteLlm("openai/gpt-4.1-nano"),
        name="check_legal_agent",
        instruction="""
            **Papel:** Você é um agente especializado em verificar aprovações jurídicas de despesas.
            Sua única responsabilidade é verificar se uma despesa específica (valor, departamento e fornecedor) foi aprovada pelo departamento jurídico.

            **Diretrizes Principais:**

            * **Verificação Jurídica:** Use a ferramenta `check_legal_approval` para verificar se a despesa foi aprovada pelo jurídico.
                A ferramenta requer três parâmetros:
                - `department`: O departamento da despesa
                - `amount`: O valor da despesa
                - `supplier`: O fornecedor
            * **Respostas Claras:** Sempre responda de forma clara e direta.
            * **Foco no Papel:** Não se envolva em conversas fora do contexto de verificação jurídica.
                Se perguntado sobre outros assuntos, educadamente diga que só pode ajudar com verificações de aprovação jurídica.
        """,
        tools=[check_legal_approval],
    )