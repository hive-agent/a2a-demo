# Check Planning Agent

Este agente é responsável por verificar se uma despesa está planejada no orçamento, utilizando dados de despesas locais. Ele faz parte de um sistema de automação financeira, mas pode ser executado de forma independente.

## Visão Geral

O agente expõe um serviço que responde se uma despesa específica (departamento, valor e fornecedor) está planejada no orçamento, consultando o arquivo de despesas. Pode ser utilizado em fluxos de controle orçamentário, análise de planejamento ou integração com outros sistemas.

## Estrutura dos Arquivos

- `main.py`: Inicializa o servidor do agente e expõe a API.
- `agent.py`: Define a lógica do agente e a função de verificação de planejamento.
- `agent_executor.py`: Executor responsável por orquestrar a execução do agente.
- `pyproject.toml` e `uv.lock`: Gerenciamento de dependências.
- `../database/espenses.csv`: Arquivo CSV contendo as despesas planejadas com departamento, valor e fornecedor.

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
pip install a2a-sdk google-adk python-dotenv pandas uvicorn litellm
```

## Como Executar

No diretório `check_planning_agent`, execute:

```bash
python main.py
```

O agente irá iniciar um servidor local (por padrão em `localhost:10003`).

## Como funciona

O agente recebe solicitações informando departamento, valor e fornecedor, e responde se a despesa está planejada no orçamento, consultando o arquivo `../database/espenses.csv`.

- Se houver uma linha correspondente com os critérios informados, responde: **"Despesa foi planejada"**
- Caso contrário, responde: **"Despesa não foi planejada"**

## Observações

- Para alterar as despesas planejadas, edite o arquivo `../database/espenses.csv`.
- O agente é focado apenas em consultas de planejamento orçamentário. Para outros tipos de análise, utilize ou integre com outros agentes.

---

Em caso de dúvidas, consulte o código-fonte ou entre em contato com o responsável pelo projeto.
