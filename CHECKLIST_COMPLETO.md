# 🔍 CHECKLIST COMPLETO DO SISTEMA - CYBERTV SUPORTE

## ✅ STATUS: EM ANDAMENTO

---

## 1. SERVIÇOS E INFRAESTRUTURA

### Backend (FastAPI)
- [ ] Servidor rodando
- [ ] Porta 8001 funcionando
- [ ] Sem erros nos logs
- [ ] Hot reload ativo

### Frontend (React)
- [ ] Servidor rodando
- [ ] Porta 3000 funcionando
- [ ] Sem erros no console
- [ ] Hot reload ativo

### MongoDB
- [ ] Serviço rodando
- [ ] Conexão estabelecida
- [ ] Collections criadas
- [ ] Índices configurados

### Nginx
- [ ] Proxy funcionando
- [ ] Rotas corretas

---

## 2. AUTENTICAÇÃO E USUÁRIOS

### Admin Principal
- [ ] Login funcionando (`102030@ab`)
- [ ] Token JWT válido
- [ ] Sessão persistente
- [ ] Logout funcionando

### Revendas
- [ ] Login unificado (`/reseller-login`)
- [ ] Email + Senha funcionando
- [ ] Primeiro login obrigatório trocar senha
- [ ] Token JWT correto
- [ ] Logout funcionando

### Atendentes
- [ ] Login funcionando
- [ ] Criação de atendentes
- [ ] Edição de atendentes
- [ ] Exclusão de atendentes

### Clientes
- [ ] Login funcionando
- [ ] Registro de novos clientes
- [ ] Sessão funcionando

---

## 3. FUNCIONALIDADES ADMIN DASHBOARD

### Aba: Revendas
- [ ] Listar todas revendas
- [ ] Criar nova revenda
- [ ] Modal com informações completas
- [ ] Botão "Copiar Tudo" funcionando
- [ ] Editar revenda
- [ ] Excluir revenda
- [ ] Visualização hierárquica (árvore)
- [ ] Botão "Aplicar para Revendas"
- [ ] Replicação de configurações

### Aba: Atendentes
- [ ] Listar atendentes
- [ ] Criar atendente
- [ ] Editar atendente
- [ ] Excluir atendente
- [ ] Upload de avatar

### Aba: Agentes IA
- [ ] Listar agentes IA
- [ ] Criar agente IA
- [ ] Configurar prompts
- [ ] Habilitar/Desabilitar
- [ ] Testar agente

### Aba: Departamentos
- [ ] Listar departamentos
- [ ] Criar departamento
- [ ] Editar departamento
- [ ] Excluir departamento

### Aba: Msg Rápidas (Quick Blocks)
- [ ] Listar mensagens rápidas
- [ ] Criar nova mensagem
- [ ] Editar mensagem
- [ ] Excluir mensagem
- [ ] Usar atalhos

### Aba: Dados Permitidos (Security)
- [ ] Configurar CPFs permitidos
- [ ] Configurar Emails permitidos
- [ ] Configurar Telefones permitidos
- [ ] Chaves aleatórias

### Aba: API
- [ ] Configurar URL da API
- [ ] Configurar Token da API
- [ ] Habilitar/Desabilitar API
- [ ] Testar conexão

### Aba: Avisos
- [ ] Criar aviso
- [ ] Publicar aviso
- [ ] Avisos aparecem para todos

### Aba: Auto-Responder
- [ ] Listar auto-respostas
- [ ] Criar auto-resposta
- [ ] Configurar gatilhos
- [ ] Editar auto-resposta
- [ ] Excluir auto-resposta
- [ ] Testar funcionamento

### Aba: Tutoriais/Apps
- [ ] Listar tutoriais
- [ ] Criar tutorial
- [ ] Upload de arquivo
- [ ] Editar tutorial
- [ ] Excluir tutorial
- [ ] Testar download

### Aba: Apps IPTV
- [ ] Listar apps IPTV
- [ ] Criar app IPTV
- [ ] Editar configurações
- [ ] Excluir app
- [ ] Automação SS-IPTV funcionando
- [ ] Outros apps (manual)

---

## 4. FUNCIONALIDADES RESELLER DASHBOARD

### Aba: Atendentes
- [ ] Funcionalidade igual ao Admin

### Aba: Agentes IA
- [ ] Funcionalidade igual ao Admin

### Aba: Departamentos
- [ ] Funcionalidade igual ao Admin

### Aba: Msg Rápidas
- [ ] Funcionalidade igual ao Admin

### Aba: Dados Permitidos
- [ ] Funcionalidade igual ao Admin

### Aba: API
- [ ] Funcionalidade igual ao Admin

### Aba: Avisos
- [ ] Funcionalidade igual ao Admin

### Aba: Auto-Responder
- [ ] Funcionalidade igual ao Admin

### Aba: Tutoriais/Apps
- [ ] Funcionalidade igual ao Admin

### Aba: Apps IPTV
- [ ] Funcionalidade igual ao Admin

### Aba: Domínio
- [ ] Ver domínio de teste
- [ ] Adicionar domínio customizado
- [ ] Instruções DNS completas
- [ ] Verificar DNS
- [ ] Ativar domínio oficial
- [ ] Desativar domínio de teste

### Pop-up DNS
- [ ] Aparece a cada 30 minutos
- [ ] Durante 24 horas
- [ ] Countdown de 30 segundos
- [ ] Instruções claras
- [ ] Para de aparecer após domínio configurado

---

## 5. CHAT E TICKETS

### Criação de Tickets
- [ ] Cliente pode criar ticket
- [ ] Ticket aparece para atendente
- [ ] Ticket aparece em "Espera"

### Atendimento
- [ ] Atendente pode pegar ticket
- [ ] Ticket vai para "Atendendo"
- [ ] Mensagens em tempo real (WebSocket)
- [ ] Enviar mensagem texto
- [ ] Enviar arquivo
- [ ] Enviar imagem
- [ ] Enviar áudio
- [ ] Receber mensagens

### Finalização
- [ ] Atendente pode finalizar ticket
- [ ] Ticket vai para "Finalizadas"
- [ ] Cliente notificado

### Notificações
- [ ] Som de notificação
- [ ] Contagem de mensagens não lidas
- [ ] Notificação browser (PWA)

---

## 6. MULTI-TENANT

### Detecção de Tenant
- [ ] Por domínio customizado
- [ ] Por domínio de teste
- [ ] Por token JWT
- [ ] Domínio master (admin)

### Isolamento de Dados
- [ ] Cada revenda vê apenas seus dados
- [ ] Admin vê todos os dados
- [ ] Tickets isolados por revenda
- [ ] Atendentes isolados por revenda

### Configurações
- [ ] Cada revenda tem sua config
- [ ] Replicação funciona
- [ ] Não afeta dados manuais

---

## 7. IPTV AUTOMAÇÃO

### SS-IPTV
- [ ] Automação funcionando
- [ ] Playwright configurado
- [ ] Browser headless OK
- [ ] Screenshots em tempo real
- [ ] Logs detalhados
- [ ] Tratamento de erros

### Outros Apps (Manual)
- [ ] SmartOne: modo manual
- [ ] Duplecast: modo manual
- [ ] Instruções claras

---

## 8. PWA (Progressive Web App)

### Configuração
- [ ] manifest.json correto
- [ ] service-worker.js funcionando
- [ ] Ícones configurados
- [ ] Nome do app correto

### Funcionalidades
- [ ] Instalar no celular
- [ ] Funcionar offline (básico)
- [ ] Push notifications
- [ ] Som de notificação

---

## 9. SEGURANÇA

### Senhas
- [ ] Hash bcrypt
- [ ] Senha forte obrigatória
- [ ] Troca obrigatória primeiro login

### JWT
- [ ] Token seguro
- [ ] Expiração configurada
- [ ] Refresh token (se aplicável)

### CORS
- [ ] Configurado corretamente
- [ ] Domínios permitidos

### Validações
- [ ] Input sanitization
- [ ] XSS protection
- [ ] SQL injection protection (MongoDB)

---

## 10. PERFORMANCE

### Backend
- [ ] Tempo de resposta < 200ms
- [ ] Sem memory leaks
- [ ] Queries otimizadas

### Frontend
- [ ] Carregamento < 3s
- [ ] Sem re-renders desnecessários
- [ ] Lazy loading de componentes

### WebSocket
- [ ] Conexões estáveis
- [ ] Reconexão automática
- [ ] Sem perda de mensagens

---

## 11. TESTES E2E

### Fluxo Completo Admin
- [ ] Login → Criar Revenda → Replicar Config → Logout

### Fluxo Completo Revenda
- [ ] Login → Criar Atendente → Configurar Domínio → Logout

### Fluxo Completo Atendente
- [ ] Login → Pegar Ticket → Responder → Finalizar → Logout

### Fluxo Completo Cliente
- [ ] Criar Ticket → Enviar Mensagem → Receber Resposta → Finalizar

---

## 12. DOCUMENTAÇÃO

- [ ] README.md atualizado
- [ ] Guia de instalação
- [ ] Guia de uso
- [ ] API endpoints documentados
- [ ] Credenciais documentadas

---

## 13. DEPLOY

- [ ] .env configurado
- [ ] Variáveis de ambiente corretas
- [ ] Sem hardcoded values
- [ ] Backup do banco
- [ ] Domínio configurado
- [ ] SSL configurado (se prod)

---

## ✅ CONCLUSÃO

**Total de itens:** ~150+
**Verificados:** Em andamento...
**Falhas:** A serem identificadas...

---

**Última atualização:** 23/10/2024
