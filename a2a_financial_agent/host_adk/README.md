# Agente Orquestrador Financeiro

Este é o agente orquestrador que coordena a aprovação de despesas de negócios, consultando múltiplos agentes especializados para tomar decisões automatizadas sobre gastos corporativos.

## Visão Geral

O **FinancialOrchestratorAgent** coordena verificações com três agentes especializados:

- **check_budget_agent** (porta 10002): Verifica se há orçamento disponível
- **check_planning_agent** (porta 10003): Verifica se a despesa está planejada
- **check_legal_agent** (porta 10004): Verifica aprovação jurídica

## Como Funciona

O orquestrador:
1. Conecta-se aos agentes especializados
2. Consulta cada agente sobre a despesa
3. Coleta as respostas
4. Toma decisão baseada nas validações:
   - ✅ **Aprovado**: Se TODOS os agentes aprovarem
   - ❌ **Rejeitado**: Se QUALQUER agente reprovar ou estiver indisponível

## Pré-requisitos

### 1. Agentes Especializados em Execução

**IMPORTANTE**: Todos os agentes devem estar executando:

```bash
# Terminal 1 - Agente de Orçamento
cd a2a_financial_agent/check_budget_agent
uv run python .\main.py

# Terminal 2 - Agente de Planejamento  
cd a2a_financial_agent/check_planning_agent
uv run python .\main.py

# Terminal 3 - Agente Jurídico
cd a2a_financial_agent/check_legal_agent
uv run python .\main.py
```

### 2. Configuração do Ambiente

- Python 3.10+
- Chave de API da OpenAI

## Instalação

```bash
cd a2a_financial_agent/host_adk
pip install .
```

## Configuração

### Arquivo .env

Crie um arquivo `.env` no diretório `host_adk`:

```bash
OPENAI_API_KEY=sua_chave_da_openai_aqui
```

**⚠️ IMPORTANTE**: Sem esta chave, o agente não funcionará.

## Como Executar

```bash
cd a2a_financial_agent/host_adk
uv run --active adk web
```

## Exemplos de Uso

### Exemplo 1: Despesa Aprovada

**Pergunta:**
```
"Posso aprovar uma despesa de R$ 2.500 do departamento de Marketing com a Agência XYZ?"
```

**Resposta Esperada:**
```
• Verificação de Orçamento: ✅ Tem budget disponível
• Verificação de Planejamento: ✅ Despesa foi planejada  
• Verificação Jurídica: ✅ Aprovado pelo jurídico

✅ DESPESA APROVADA
Todos os agentes aprovaram a despesa.
```

### Exemplo 2: Despesa Rejeitada

**Pergunta:**
```
"Posso aprovar uma despesa de R$ 15.000 do departamento de Finance?"
```

**Resposta Esperada:**
```
• Verificação de Orçamento: ❌ Não tem budget disponível
• Verificação de Planejamento: ✅ Despesa foi planejada
• Verificação Jurídica: ✅ Aprovado pelo jurídico

❌ DESPESA REJEITADA
Motivo: Orçamento insuficiente.
```

## Observações Importantes

- **Todos os agentes devem estar rodando** para funcionamento correto
- **A despesa só é aprovada** se TODOS os agentes aprovarem
- **Qualquer agente indisponível** resulta em rejeição automática

---

Para dúvidas, consulte os READMEs individuais de cada agente especializado. 