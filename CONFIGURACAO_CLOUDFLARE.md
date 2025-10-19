# 🌐 Configuração DNS Cloudflare - suporte.help

## 📋 Registros DNS Necessários

### ✅ Configuração Completa

| Tipo | Nome | Conteúdo/Destino | Proxy Status | TTL |
|------|------|------------------|--------------|-----|
| A | @ | 34.57.15.54 | 🔴 DNS only (cinza) | Auto |
| CNAME | www | suporte.help | 🔴 DNS only | Auto |
| CNAME | atendente | suporte.help | 🔴 DNS only | Auto |
| CNAME | admin | suporte.help | 🔴 DNS only | Auto |
| NS | - | ian.ns.cloudflare.com | - | - |
| NS | - | maya.ns.cloudflare.com | - | - |

---

## 🔧 Passo a Passo Detalhado

### 1️⃣ **Deletar Registros Antigos (se existirem)**

Antes de adicionar os novos, DELETE qualquer registro A ou CNAME antigo que aponte para:
- Servidor antigo
- IP diferente de 34.57.15.54

**Como deletar:**
- Clique no registro
- Clique em "Delete"
- Confirme

---

### 2️⃣ **Adicionar Registro Principal (Domínio Raiz)**

**Configuração:**
```
Tipo: A
Nome: @ (ou deixe em branco, significa raiz do domínio)
IPv4 address: 34.57.15.54
Proxy status: DNS only (nuvem CINZA, NÃO laranja)
TTL: Auto
```

**Clique em "Save"**

✅ Isso fará `https://suporte.help` funcionar

---

### 3️⃣ **Adicionar WWW (Opcional mas recomendado)**

**Configuração:**
```
Tipo: CNAME
Nome: www
Target: suporte.help
Proxy status: DNS only
TTL: Auto
```

**Clique em "Save"**

✅ Isso fará `https://www.suporte.help` redirecionar para `https://suporte.help`

---

### 4️⃣ **Adicionar Subdomínio Atendente**

**Configuração:**
```
Tipo: CNAME
Nome: atendente
Target: suporte.help
Proxy status: DNS only
TTL: Auto
```

**Clique em "Save"**

✅ Isso permitirá acessar: `https://atendente.suporte.help/login`

---

### 5️⃣ **Adicionar Subdomínio Admin**

**Configuração:**
```
Tipo: CNAME
Nome: admin
Target: suporte.help
Proxy status: DNS only
TTL: Auto
```

**Clique em "Save"**

✅ Isso permitirá acessar: `https://admin.suporte.help/login`

---

## ⚠️ ATENÇÃO: Proxy Status

**MUITO IMPORTANTE:**
- Deixe o **Proxy Status** em **DNS only** (nuvem CINZA)
- NÃO ative o proxy laranja da Cloudflare
- Isso evita conflitos com o SSL da Emergent

Se estiver laranja (Proxied), clique para mudar para cinza (DNS only)

---

## 🔍 Como Verificar se Está Correto

Após salvar, seus registros devem aparecer assim:

```
✅ A      @          34.57.15.54           DNS only
✅ CNAME  www        suporte.help          DNS only
✅ CNAME  atendente  suporte.help          DNS only
✅ CNAME  admin      suporte.help          DNS only
   NS     -          ian.ns.cloudflare.com
   NS     -          maya.ns.cloudflare.com
```

---

## ⏱️ Tempo de Propagação

- **Mínimo:** 5 minutos
- **Normal:** 15-30 minutos
- **Máximo:** 1-2 horas

---

## 🧪 Testar se Funcionou

Após 15 minutos, abra o terminal e digite:

```bash
# Verificar DNS
nslookup suporte.help

# Deve retornar: 34.57.15.54

# Verificar acesso
curl -I https://suporte.help
```

Ou simplesmente acesse no navegador:
- https://suporte.help

---

## 🆘 Problemas Comuns

### "ERR_NAME_NOT_RESOLVED"
**Solução:** Aguarde mais tempo (até 1 hora)

### "Certificado SSL inválido"
**Solução:** 
1. Certifique-se que fez deploy na Emergent
2. Vincule o domínio customizado na Emergent
3. Aguarde SSL ser gerado (pode levar até 24h)

### "Página não carrega / Timeout"
**Solução:**
1. Verifique se Proxy Status está em **DNS only** (cinza)
2. Certifique-se que o IP é exatamente: `34.57.15.54`
3. Aguarde propagação DNS

### "Still showing old website"
**Solução:**
1. Limpe cache do navegador (Ctrl + Shift + Delete)
2. Teste em aba anônima
3. Limpe cache DNS do computador:
   - Windows: `ipconfig /flushdns`
   - Mac: `sudo dscacheutil -flushcache`
   - Linux: `sudo systemd-resolve --flush-caches`

---

## ✅ Próximo Passo

Após configurar o DNS na Cloudflare, você precisa:

**Vincular o domínio na Emergent:**
1. Vá no painel da Emergent
2. Clique em "Deploy" (se ainda não fez)
3. Vá em "Deployments" → "Custom Domain"
4. Clique "Link Domain"
5. Digite: `suporte.help`
6. Aguarde verificação

---

## 📞 Suporte

Se tiver dúvidas:
1. Tire print da tela DNS da Cloudflare
2. Execute: `/app/verificar_dominio.sh`
3. Envie os resultados
