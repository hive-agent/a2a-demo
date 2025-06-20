# Check Budget Agent

Este agente é responsável por verificar se há orçamento disponível para um valor solicitado, utilizando dados financeiros locais. Ele faz parte de um sistema de automação financeira, mas pode ser executado de forma independente.

## Visão Geral

O agente expõe um serviço que responde se existe budget disponível para um valor informado, consultando o arquivo de orçamento atual. Ele pode ser utilizado em fluxos de aprovação de despesas, automação de processos financeiros ou integração com outros sistemas.

## Estrutura dos Arquivos

- `main.py`: Inicializa o servidor do agente e expõe a API.
- `agent.py`: Define a lógica do agente e a função de verificação de orçamento.
- `agent_executor.py`: Executor responsável por orquestrar a execução do agente.
- `pyproject.toml` e `uv.lock`: Gerenciamento de dependências.
- `../database/current_budget.txt`: Arquivo de texto contendo o valor atual do orçamento disponível (um número).
- `../database/expenses.csv`: Exemplo de arquivo de despesas (não utilizado diretamente pelo agente, mas pode ser útil para contexto ou integrações futuras).

## Pré-requisitos

- Python 3.8 ou superior
- Recomenda-se o uso de ambiente virtual (venv)

## Instalação das Dependências

No diretório do agente, execute:

```bash
pip install -r requirements.txt  # ou utilize o pyproject.toml com o gerenciador de sua preferência
```

Se não houver um requirements.txt, use:

```bash
pip install a2a-sdk google-adk python-dotenv uvicorn litellm
```

## Como Executar

No diretório `check_budget_agent`, execute:

```bash
python main.py
```

O agente irá iniciar um servidor local (por padrão em `localhost:10002`).

## Como funciona

O agente recebe solicitações informando um valor e responde se há orçamento disponível, consultando o valor em `../database/current_budget.txt`.

- Se o valor solicitado for menor ou igual ao orçamento disponível, responde: **"Tem budget disponível"**
- Caso contrário, responde: **"Não tem budget disponível"**

## Observações

- Para alterar o orçamento disponível, edite o valor no arquivo `../database/current_budget.txt`.
- O agente é focado apenas em consultas de disponibilidade de orçamento. Para outros tipos de análise financeira, utilize ou integre com outros agentes.

---

Em caso de dúvidas, consulte o código-fonte ou entre em contato com o responsável pelo projeto.
