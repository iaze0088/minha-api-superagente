# 🌐 Como Usar Seu Domínio Próprio (suporte.help)

## Método 1: Cloudflare (Recomendado)

### Passo 1: Obter IP do Servidor
```bash
# No terminal do servidor, execute:
curl ifconfig.me
```
Exemplo de resultado: `203.0.113.45`

### Passo 2: Configurar no Cloudflare

1. Acesse [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Selecione seu domínio: `suporte.help`
3. Vá em **DNS** → **Records**
4. Adicione os seguintes registros:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | `IP_DO_SERVIDOR` | ✅ Proxied | Auto |
| CNAME | www | suporte.help | ✅ Proxied | Auto |
| CNAME | atendente | suporte.help | ✅ Proxied | Auto |
| CNAME | admin | suporte.help | ✅ Proxied | Auto |

### Passo 3: Configurar SSL/TLS
1. No Cloudflare, vá em **SSL/TLS**
2. Selecione modo: **Full (strict)**
3. Ative **Always Use HTTPS**

### Passo 4: Atualizar Backend (.env)
```bash
# Edite /app/backend/.env
nano /app/backend/.env

# Altere a linha:
REACT_APP_BACKEND_URL="https://suporte.help"
```

### Passo 5: Reiniciar Serviços
```bash
sudo supervisorctl restart backend frontend
```

---

## Método 2: Subdomínios por Revenda

### Exemplo de Estrutura:
- `suporte.help` → Admin principal
- `revenda1.suporte.help` → Revenda 1
- `revenda2.suporte.help` → Revenda 2
- `clientefinal.suporte.help` → Cliente da Revenda

### Cloudflare para Revendas:
```
Type: CNAME
Name: *
Content: suporte.help
Proxy: ✅ Proxied
```

Isso permite criar infinitos subdomínios automaticamente!

---

## Método 3: Emergent Custom Domain (Se disponível)

Se a Emergent oferece domínio customizado:

1. Vá no painel Emergent
2. Settings → Custom Domain
3. Adicione: `suporte.help`
4. Configure DNS conforme instruções da Emergent

---

## ⚠️ IMPORTANTE

**Não use URLs hardcoded no código!**

✅ CORRETO:
```javascript
const API_URL = process.env.REACT_APP_BACKEND_URL;
```

❌ ERRADO:
```javascript
const API_URL = "https://iptv-support-hub.preview.emergentagent.com";
```

---

## 🧪 Testar Após Configurar

```bash
# Testar resolução DNS
ping suporte.help

# Testar API
curl https://suporte.help/api/agents

# Testar frontend
curl -I https://suporte.help
```

---

## 📞 Suporte

Se precisar de ajuda:
- Verifique logs: `tail -f /var/log/supervisor/backend.err.log`
- Status serviços: `sudo supervisorctl status`
