# 🚀 Deploy Rápido - 5 Minutos

## ⚡ Comandos Rápidos

### 1️⃣ Apontar DNS (Fazer no Painel do Domínio)

```
Tipo: A
Host: att.suporte.help
Valor: 157.180.19.132
TTL: Automático
```

### 2️⃣ Copiar Arquivos para o Servidor

```bash
# Do seu computador local
scp -r backend frontend deploy.sh root@157.180.19.132:/app/
```

### 3️⃣ Conectar e Executar

```bash
ssh root@157.180.19.132
# Senha: 102030ab

cd /app
chmod +x deploy.sh
./deploy.sh
```

### 4️⃣ Aguardar e Pronto! ✅

Tempo: ~10 minutos

Ao final, acesse: **https://att.suporte.help**

---

## 🔑 Credenciais Padrão

**Admin:**
- Email: `admin@admin.com`
- Senha: `admin123`

⚠️ Altere após primeiro login!

---

## 🛠️ Comandos Úteis Pós-Deploy

```bash
# Ver logs backend
tail -f /var/log/cybertv-backend.out.log

# Reiniciar backend
supervisorctl restart cybertv-backend

# Reiniciar Nginx
systemctl restart nginx

# Status de tudo
supervisorctl status
```

---

## ❓ Problemas?

**SSL não configurou?**
```bash
# DNS ainda não propagou, aguarde e execute:
certbot --nginx -d att.suporte.help --non-interactive --agree-tos --email admin@suporte.help --redirect
```

**Backend não inicia?**
```bash
# Ver erro:
tail -f /var/log/cybertv-backend.err.log

# Reinstalar:
cd /var/www/cybertv-suporte/backend
pip3 install -r requirements.txt
supervisorctl restart cybertv-backend
```

---

✅ **Documentação Completa:** Veja `README_DEPLOYMENT.md`
