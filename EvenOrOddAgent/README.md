# Agente Par ou Ímpar

Este é um agente simples que determina se um número é par ou ímpar. O projeto demonstra a implementação de um agente usando o framework A2A (Agent-to-Agent).

## Funcionalidades

- O agente recebe um número como entrada
- Determina se o número é par ou ímpar
- Retorna o resultado em formato de texto

## Estrutura do Projeto

- `main.py`: Implementação do servidor do agente
- `agent_executor.py`: Lógica do agente para determinar se um número é par ou ímpar
- `test_client.py`: Cliente de teste que envia números para o agente

## Instalação

1. Crie um ambiente virtual:
```bash
uv venv
```

2. Ative o ambiente virtual:
```bash
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

## Executando o Projeto

1. Em um terminal, inicie o servidor do agente:
```bash
uv run python .\main.py
```

2. Em outro terminal, execute o cliente de teste:
```bash
uv run python .\test_client.py
```

O cliente enviará o número "12" para o agente, que responderá indicando se é par ou ímpar.

## Como Funciona

1. O servidor (`main.py`) cria uma instância do agente e o expõe através de uma API HTTP
2. O agente (`agent_executor.py`) processa a entrada e determina se o número é par ou ímpar
3. O cliente de teste (`test_client.py`) envia uma requisição para o agente e exibe a resposta

## Tecnologias Utilizadas

- Python 3.13+
- A2A SDK
- Uvicorn (servidor ASGI)
- HTTPX (cliente HTTP assíncrono)
