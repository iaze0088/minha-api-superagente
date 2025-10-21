# 🤖 Monitoramento de Logs da IA

## 📋 O que é?

Criamos um sistema completo de logging para monitorar o comportamento da IA em tempo real. Todos os eventos relacionados ao processamento de mensagens pela IA são registrados em um arquivo dedicado.

## 📁 Arquivo de Log

**Localização**: `/var/log/ai_agent.log`

## 🔍 Como Visualizar os Logs

### 1. Ver as últimas 50 linhas do log
```bash
tail -n 50 /var/log/ai_agent.log
```

### 2. Monitorar em tempo real (acompanhar novas entradas)
```bash
tail -f /var/log/ai_agent.log
```

### 3. Pesquisar por palavra-chave específica
```bash
grep "ERRO" /var/log/ai_agent.log
grep "IA ativada" /var/log/ai_agent.log
grep "BLOQUEIO" /var/log/ai_agent.log
```

### 4. Ver todo o log
```bash
cat /var/log/ai_agent.log
```

## 📊 Legendas dos Marcadores

O sistema usa emojis para facilitar a identificação rápida dos eventos:

- 🟢 = Início de processamento de nova mensagem
- 🔍 = Investigação/verificação
- ✅ = Sucesso/verificação passou
- ❌ = Falha/bloqueio
- 🤖 = IA respondendo
- ⚠️ = Aviso
- 💥 = Erro crítico
- 📋 = Informação
- 🎉 = Processo completo com sucesso
- 🔴 = Fim de processo (bloqueado)

## 📝 Exemplo de Fluxo Completo

Quando um cliente envia uma mensagem, você verá logs como este:

```
2025-01-21 10:30:45 [INFO] 🟢 ================================================================================
2025-01-21 10:30:45 [INFO] 🔍 NOVA MENSAGEM RECEBIDA PARA PROCESSAMENTO IA
2025-01-21 10:30:45 [INFO] 📋 Ticket ID: abc-123
2025-01-21 10:30:45 [INFO] 👤 Cliente: João Silva
2025-01-21 10:30:45 [INFO] 🏢 Reseller ID: null
2025-01-21 10:30:45 [INFO] 💬 Mensagem: Olá, preciso de ajuda...
2025-01-21 10:30:45 [INFO] 📂 Verificando departamento...
2025-01-21 10:30:45 [INFO]    Department ID: SUPORTE
2025-01-21 10:30:45 [INFO] ✅ Departamento encontrado:
2025-01-21 10:30:45 [INFO]    Nome: SUPORTE
2025-01-21 10:30:45 [INFO]    AI Agent ID: 55a70e0e-bddd-46fa-a34f-642c1d0b3ef4
2025-01-21 10:30:45 [INFO] 🔎 Buscando agente IA no banco de dados...
2025-01-21 10:30:45 [INFO] ✅ Agente IA encontrado:
2025-01-21 10:30:45 [INFO]    Nome: Suporte
2025-01-21 10:30:45 [INFO]    Ativo: True
2025-01-21 10:30:45 [INFO]    Modelo: openai/gpt-4o-mini
2025-01-21 10:30:45 [INFO] 🎉 TODAS AS VERIFICAÇÕES PASSARAM!
2025-01-21 10:30:45 [INFO] 🚀 Chamando serviço de IA para gerar resposta...
2025-01-21 10:30:45 [INFO] ================================================================================
2025-01-21 10:30:45 [INFO] 🤖 INICIANDO GERAÇÃO DE RESPOSTA DA IA
2025-01-21 10:30:45 [INFO] 📝 Mensagem recebida: Olá, preciso de ajuda...
2025-01-21 10:30:45 [INFO] 🔑 API Key presente: sk-emergen...F32621
2025-01-21 10:30:46 [INFO] ✅ RESPOSTA RECEBIDA DO LLM!
2025-01-21 10:30:46 [INFO] 📤 Resposta (150 caracteres): Olá! Como posso te ajudar hoje?...
2025-01-21 10:30:46 [INFO] ✅ Mensagem da IA salva com sucesso
2025-01-21 10:30:46 [INFO] 🎉 PROCESSO COMPLETO! IA respondeu com sucesso
2025-01-21 10:30:46 [INFO] 🟢 ================================================================================
```

## 🚨 Cenários de Bloqueio

Se a IA **não responder**, o log mostrará exatamente o motivo:

### Exemplo 1: Ticket sem departamento
```
2025-01-21 10:35:00 [INFO] ❌ BLOQUEIO: Ticket abc-456 sem departamento atribuído
2025-01-21 10:35:00 [INFO] 💡 Ação necessária: Cliente deve selecionar um departamento
2025-01-21 10:35:00 [INFO] 🔴 ================================================================================
```

### Exemplo 2: IA desativada manualmente
```
2025-01-21 10:40:00 [INFO] ❌ IA DESATIVADA MANUALMENTE para ticket abc-789 até 2025-01-21 11:40:00
2025-01-21 10:40:00 [INFO] 🔴 ================================================================================
```

### Exemplo 3: Atendente não na lista de linked_agents
```
2025-01-21 10:45:00 [INFO] ❌ BLOQUEIO: Atendente xyz-123 não está na lista de linked_agents
2025-01-21 10:45:00 [INFO] 💡 Ação necessária: Adicionar atendente à lista de linked_agents do agente IA
2025-01-21 10:45:00 [INFO] 🔴 ================================================================================
```

## 💡 Dicas de Uso

1. **Para monitorar em tempo real enquanto testa**:
   ```bash
   tail -f /var/log/ai_agent.log
   ```
   Deixe este comando rodando em um terminal enquanto você interage com o chat.

2. **Para buscar problemas específicos**:
   ```bash
   grep "💥\|❌\|ERRO" /var/log/ai_agent.log
   ```

3. **Para ver só sucessos**:
   ```bash
   grep "✅\|🎉" /var/log/ai_agent.log
   ```

## 🔧 Informações Técnicas

- O log é configurado em `/app/backend/ai_service.py` e `/app/backend/server.py`
- Formato: `YYYY-MM-DD HH:MM:SS [LEVEL] message`
- O arquivo persiste entre restarts do backend
- Não há rotação automática (se crescer muito, pode ser limpo manualmente)

## 🧹 Limpar o Log

Se o arquivo ficar muito grande:
```bash
sudo truncate -s 0 /var/log/ai_agent.log
```

ou

```bash
sudo rm /var/log/ai_agent.log
sudo touch /var/log/ai_agent.log
sudo chmod 666 /var/log/ai_agent.log
```

---

**Nota**: Este sistema de logging foi criado para facilitar o diagnóstico e monitoramento da IA. Todos os eventos importantes são registrados com detalhes suficientes para identificar problemas rapidamente.
