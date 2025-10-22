# 🚀 Guia de Automação IPTV - Sistema Robusto

## ✨ Novo Sistema Implementado

Foi implementado um sistema **ROBUSTO e INTELIGENTE** de automação para configuração de apps IPTV, com as seguintes características:

### 🎯 Funcionalidades

1. **Automação Inteligente com Playwright**
   - Sistema de retry automático (até 3 tentativas)
   - Validação de cada etapa
   - Captura de screenshots de progresso
   - Logs detalhados em tempo real
   - Score de automatizabilidade (0-100%)

2. **Fallback Automático para Modo Manual**
   - Se a automação falhar, o sistema automaticamente sugere o modo manual
   - Interface guiada passo-a-passo para configuração manual

3. **Apps Suportados**
   - ✅ **SS-IPTV** (automação completa)
   - ✅ **SmartOne IPTV** (automação completa)
   - ⏳ **Duplex Play, IBO Player, Smart IPTV, Bay TV, Duplecast** (modo manual guiado)

---

## 📋 Como Testar

### Passo 1: Login como Agente
1. Acesse: `https://seu-dominio.com/atendente/login`
2. Entre com suas credenciais de agente

### Passo 2: Acessar "Subir Listas"
1. No dashboard do agente, procure o botão **"Subir Listas"** no header
2. Clique para abrir o modal de apps IPTV

### Passo 3: Selecionar App
1. Escolha um dos apps disponíveis (recomendamos começar com **SS-IPTV**)
2. O modal mostrará os campos necessários

### Passo 4: Testar Automação (SS-IPTV)

**Credenciais para teste fornecidas pelo usuário:**
- Usuario: `3334567oro`
- Senha: `3334567oro`
- URL Base: `http://hplay2.xyz`
- Código SSIPTV: `PLDG` *(uso único - gerar novo se necessário)*

**Passos:**
1. Preencha os campos:
   - **Código:** `PLDG`
   - **Username:** `3334567oro`
   - **Password:** `3334567oro`

2. Clique no botão verde **"⚡ Configurar Automaticamente"**

3. Aguarde a automação executar:
   - Você verá logs em tempo real aparecerem em um terminal escuro
   - O sistema tentará preencher todos os campos automaticamente
   - Screenshots serão capturados a cada etapa

4. Resultado:
   - ✅ **Sucesso:** Mostrará mensagem de sucesso com a URL final gerada e o score de automação
   - ⚠️ **Falha:** Mostrará os logs de erro e sugerirá usar o modo manual abaixo

### Passo 5: Modo Manual (se automação falhar)

Se a automação não funcionar, você verá o divisor **"OU CONFIGURE MANUALMENTE"** e poderá:

1. Clicar no botão azul **"Abrir SS-IPTV 🚀"** (abre site em nova aba)
2. Copiar cada campo clicando nos botões **"Copiar"**
3. Colar manualmente no site
4. Copiar a URL final gerada

---

## 🔧 Para Desenvolvedores

### Arquivos Modificados

1. **Backend:**
   - `/app/backend/iptv_automation_service.py` *(NOVO)*
     - Serviço robusto de automação
     - Classes: `IPTVAutomationBase`, `SSIPTVAutomation`, `SmartOneAutomation`
     - Sistema de retry e validação
   
   - `/app/backend/server.py`
     - Endpoint `/api/iptv-apps/{app_id}/automate` melhorado
     - Usa novo serviço de automação
     - Retorna logs, screenshots e score

2. **Frontend:**
   - `/app/frontend/src/pages/AgentDashboard.js`
     - Botão "Configuração Automática" adicionado
     - Modal de progresso com logs em tempo real
     - Exibição de resultado da automação
     - Divisor "OU CONFIGURE MANUALMENTE"

### Como Adicionar Novos Apps

Para adicionar automação para um novo app (ex: Duplex Play):

1. Criar nova classe em `iptv_automation_service.py`:

```python
class DuplexPlayAutomation(IPTVAutomationBase):
    """Automação específica para Duplex Play"""
    
    async def run_automation(self):
        self.result.add_log("🔧 Iniciando automação Duplex Play...")
        
        # Navegar para o site
        config_url = self.app_data.get('config_url')
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.take_screenshot("Página inicial")
        
        # Implementar lógica específica do app...
        # - Preencher campos
        # - Clicar botões
        # - Gerar URL
        
        self.result.automation_score = 75  # Definir score
```

2. Registrar no Factory:

```python
automations = {
    "SSIPTV": SSIPTVAutomation,
    "SMARTONE": SmartOneAutomation,
    "DUPLEXPLAY": DuplexPlayAutomation,  # ADICIONAR AQUI
}
```

---

## 🎯 Próximos Passos

1. **Testar com credenciais reais**
   - Usuário deve testar com o código SSIPTV: `PLDG`
   - Se funcionar, gerar novo código e testar novamente

2. **Implementar automação para mais apps**
   - Duplex Play
   - IBO Player
   - Smart IPTV
   - Bay TV
   - Duplecast

3. **Melhorias futuras**
   - WebSocket para progresso em tempo real
   - Histórico de configurações
   - Validação de URL após configuração

---

## 📞 Suporte

Se encontrar algum problema:
1. Verificar logs no console do navegador (F12)
2. Verificar logs do backend: `tail -f /var/log/supervisor/backend.err.log`
3. Reportar issue com screenshots e logs

---

## 🎉 Resultado Esperado

Quando tudo funcionar:
- ✅ Botão de automação visível e funcional
- ✅ Logs aparecem em tempo real durante automação
- ✅ Resultado final mostra sucesso ou falha claramente
- ✅ Se falhar, modo manual é sugerido automaticamente
- ✅ Sistema é robusto e não quebra facilmente
