# 🌐 Configurar Domínio da Revenda: ajuda.vip

## ✅ Revenda Criada:

**Nome:** Revenda Teste 1
**Email:** revenda1@teste.com
**Domínio:** ajuda.vip ✓ (salvo no sistema)

---

## 📋 Configuração DNS no Cloudflare (ajuda.vip)

### Passo 1: Acessar Cloudflare
1. https://dash.cloudflare.com
2. Clique no domínio **ajuda.vip**
3. Menu: **DNS** → **Records**

### Passo 2: Adicionar Registro A
```
Tipo: A
Nome: @
IPv4 address: 34.57.15.54
Proxy status: Somente DNS (nuvem cinza)
TTL: Auto
```
Clique **"Save"**

### Passo 3: Adicionar CNAME (opcional)
```
Tipo: CNAME
Nome: www
Conteúdo: ajuda.vip
Proxy: Somente DNS
```

---

## 🔑 Login da Revenda

**URL:** https://suporte.help/revenda/login (ou https://ajuda.vip/revenda/login após DNS)
**Email:** revenda1@teste.com
**Senha:** senha123

---

## ⏱️ Tempo de Propagação

Após configurar DNS:
- Mínimo: 5-15 minutos
- Normal: 30 minutos
- Máximo: 2 horas

---

## 🧪 Testar

```bash
# Ver se DNS resolveu
nslookup ajuda.vip

# Deve retornar: 34.57.15.54
```

---

## 📱 Acesso

Após DNS propagar:
- **Cliente:** https://ajuda.vip/
- **Atendente:** https://ajuda.vip/atendente/login  
- **Revenda:** https://ajuda.vip/revenda/login

Ou use enquanto DNS não propaga:
- https://suporte.help/revenda/login
