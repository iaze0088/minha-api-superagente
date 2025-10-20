# GUIA: Configurar Domínio Customizado para Revendas
# Sistema Multi-Tenant CYBERTV Suporte

## PASSO 1: Configurar DNS do Domínio (ajuda.vip)

### No Cloudflare (ou seu provedor de DNS):

1. **Acesse o painel do Cloudflare**
   - Vá para: https://dash.cloudflare.com
   - Selecione o domínio `ajuda.vip`

2. **Adicionar Registro DNS**
   - Clique em "DNS" no menu
   - Clique em "Add record"
   
   **Registro Principal:**
   ```
   Type: A
   Name: @ (ou deixe em branco)
   IPv4 address: [SEU_IP_DO_SERVIDOR]
   Proxy status: ✅ Proxied (laranja)
   TTL: Auto
   ```

   **Registro WWW (opcional):**
   ```
   Type: A
   Name: www
   IPv4 address: [SEU_IP_DO_SERVIDOR]
   Proxy status: ✅ Proxied (laranja)
   TTL: Auto
   ```

3. **Verificar IP do Servidor**
   Para descobrir o IP do seu servidor emergent:
   - Acesse: https://suporte.help
   - Abra o console do navegador (F12)
   - Digite: `fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>console.log(d.ip))`
   - Ou pergunte ao suporte da Emergent

---

## PASSO 2: Configurar SSL no Cloudflare

1. **SSL/TLS Settings**
   - Vá para: SSL/TLS > Overview
   - Configure: **Full (strict)** ou **Full**

2. **Always Use HTTPS**
   - Vá para: SSL/TLS > Edge Certificates
   - Ative: "Always Use HTTPS" ✅

3. **Aguardar Propagação**
   - Tempo: 5-15 minutos
   - Verifique em: https://www.whatsmydns.net/#A/ajuda.vip

---

## PASSO 3: Testar o Domínio

Após configurar o DNS, teste:

```bash
# 1. Verificar se o domínio resolve
ping ajuda.vip

# 2. Verificar SSL
curl -I https://ajuda.vip

# 3. Testar no navegador
https://ajuda.vip
https://ajuda.vip/admin
https://ajuda.vip/atendente
```

---

## PASSO 4: Configurar Múltiplos Domínios de Revendas

Para cada nova revenda com domínio próprio:

1. **No Admin Dashboard (suporte.help/admin)**
   - Vá na aba "Revendas"
   - Crie a revenda
   - Preencha o campo "Domínio (opcional)" com o domínio (ex: outro.com)

2. **No DNS de cada domínio**
   - Repita os passos 1 e 2 acima
   - Aponte o domínio para o MESMO IP do servidor

3. **Middleware Automático**
   - O sistema detecta automaticamente pelo domínio
   - Cada revenda vê apenas seus dados
   - Isolamento total garantido

---

## ESTRUTURA FINAL

```
suporte.help (Admin Master)
├── /admin → Painel master
├── /atendente → Atendentes master
└── / → Clientes master

ajuda.vip (Revenda 1 - Michaelrv)
├── /admin → Admin da revenda
├── /atendente → Atendentes da revenda
└── / → Clientes da revenda

outro.com (Revenda 2)
├── /admin → Admin da revenda
├── /atendente → Atendentes da revenda
└── / → Clientes da revenda
```

---

## TROUBLESHOOTING

### Erro "SSL handshake failed"
**Causa:** DNS não configurado ou SSL não ativo
**Solução:** 
1. Verificar se o registro A está correto
2. Verificar se Cloudflare Proxy está ativo (laranja)
3. Aguardar propagação (até 24h em casos raros)

### Erro "This site can't be reached"
**Causa:** DNS não propagado
**Solução:**
1. Verificar em: https://www.whatsmydns.net
2. Aguardar propagação
3. Limpar cache DNS: `ipconfig /flushdns` (Windows) ou `sudo dscacheutil -flushcache` (Mac)

### Domínio carrega mas mostra site errado
**Causa:** IP incorreto no DNS
**Solução:**
1. Verificar IP correto do servidor
2. Atualizar registro A no DNS

---

## VERIFICAÇÃO FINAL

✅ DNS configurado corretamente
✅ SSL ativo (cadeado verde no navegador)
✅ https://ajuda.vip carrega a página do chat
✅ https://ajuda.vip/admin carrega painel da revenda
✅ Dados isolados (revenda só vê seus próprios dados)

---

## IMPORTANTE

⚠️ **Cada domínio de revenda precisa:**
1. Ser registrado e de propriedade do cliente/revenda
2. Ter DNS apontando para seu servidor
3. Ser adicionado no campo "custom_domain" no Admin Dashboard

⚠️ **O servidor Emergent suporta múltiplos domínios automaticamente**
- Não precisa configuração adicional no servidor
- O middleware detecta automaticamente
- Isolamento de dados é garantido pelo backend

---

## SUPORTE

Se após 24h o domínio ainda não funcionar:
1. Verificar registros DNS no Cloudflare
2. Testar com: `nslookup ajuda.vip`
3. Verificar se o IP está correto
4. Entrar em contato com suporte da Emergent
