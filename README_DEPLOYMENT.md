# 🚀 Guia de Deploy - CYBERTV Suporte

## 📋 Informações do Servidor

- **IP:** 157.180.19.132
- **Domínio:** att.suporte.help
- **Usuário:** root
- **Senha:** 102030ab

## 🎯 O que o Script Faz

O script `deploy.sh` realiza um deployment completo e automatizado:

1. ✅ Atualiza o sistema operacional
2. ✅ Instala Node.js 18.x e Yarn
3. ✅ Instala Python 3.10+
4. ✅ Instala e configura MongoDB localmente
5. ✅ Instala e configura Nginx como reverse proxy
6. ✅ Instala Certbot e configura SSL automático (Let's Encrypt)
7. ✅ Instala Supervisor para gerenciar processos
8. ✅ Copia e configura o código da aplicação
9. ✅ Instala todas as dependências (Python e Node)
10. ✅ Faz o build do frontend React
11. ✅ Configura variáveis de ambiente automaticamente
12. ✅ Inicia todos os serviços

## 🔧 Pré-requisitos

### 1. Apontar o Domínio para o IP

Antes de executar o script, você precisa configurar o DNS do domínio:

**No painel do seu registrador de domínio (ex: Registro.br, GoDaddy, etc):**

- Criar um registro `A` apontando `att.suporte.help` para `157.180.19.132`
- Aguardar propagação DNS (pode levar até 24h, mas geralmente 10-30 minutos)

**Verificar se o DNS propagou:**
```bash
ping att.suporte.help
```

### 2. Sistema Operacional

O script foi testado em:
- Ubuntu 20.04 LTS
- Ubuntu 22.04 LTS
- Debian 11+

## 📦 Preparação dos Arquivos

### Opção 1: Copiar via SCP (Recomendado)

```bash
# No seu computador local (dentro da pasta do projeto)
scp -r backend frontend deploy.sh root@157.180.19.132:/app/
```

### Opção 2: Clonar via Git

Se você tem o código em um repositório Git:

```bash
ssh root@157.180.19.132
git clone SEU_REPOSITORIO /app
```

## 🚀 Executar o Deploy

### Passo 1: Conectar ao Servidor

```bash
ssh root@157.180.19.132
# Senha: 102030ab
```

### Passo 2: Navegar até o diretório

```bash
cd /app
```

### Passo 3: Dar permissão de execução

```bash
chmod +x deploy.sh
```

### Passo 4: Executar o script

```bash
./deploy.sh
```

**O script vai:**
- Instalar tudo automaticamente
- Configurar SSL
- Iniciar todos os serviços
- Exibir um resumo ao final

**Tempo estimado:** 10-15 minutos

## 🎉 Após o Deploy

### Acessar a Aplicação

🌐 **URL:** https://att.suporte.help

### Credenciais de Admin Padrão

- **Email:** admin@admin.com
- **Senha:** admin123

⚠️ **IMPORTANTE:** Altere a senha do admin após o primeiro login!

## 🔍 Verificar Status dos Serviços

```bash
# Status de todos os serviços
supervisorctl status

# Ver logs do backend
tail -f /var/log/cybertv-backend.out.log

# Ver erros do backend
tail -f /var/log/cybertv-backend.err.log

# Status do Nginx
systemctl status nginx

# Status do MongoDB
systemctl status mongod
```

## 🛠️ Comandos Úteis

### Reiniciar Serviços

```bash
# Reiniciar backend
supervisorctl restart cybertv-backend

# Reiniciar Nginx
systemctl restart nginx

# Reiniciar MongoDB
systemctl restart mongod
```

### Atualizar Código

```bash
cd /var/www/cybertv-suporte

# Atualizar backend
cd backend
git pull  # ou copie os novos arquivos
pip3 install -r requirements.txt
supervisorctl restart cybertv-backend

# Atualizar frontend
cd ../frontend
git pull  # ou copie os novos arquivos
yarn install
yarn build
systemctl restart nginx
```

### Ver Logs em Tempo Real

```bash
# Backend
tail -f /var/log/cybertv-backend.out.log

# Nginx access
tail -f /var/log/nginx/access.log

# Nginx error
tail -f /var/log/nginx/error.log
```

## 🔒 Segurança

### Firewall (Recomendado)

```bash
# Instalar UFW
apt-get install -y ufw

# Configurar regras
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Ativar firewall
ufw enable

# Ver status
ufw status
```

### Alterar Senha do Root

```bash
passwd root
```

### Criar Usuário Não-Root (Recomendado)

```bash
adduser deploy
usermod -aG sudo deploy
```

## 🐛 Troubleshooting

### Problema: SSL não configurou

**Causa:** DNS ainda não propagou

**Solução:**
```bash
# Verificar se o domínio aponta para o IP
ping att.suporte.help

# Se ainda não propagou, aguarde e execute:
certbot --nginx -d att.suporte.help --non-interactive --agree-tos --email admin@suporte.help --redirect
```

### Problema: Backend não inicia

**Solução:**
```bash
# Ver logs de erro
tail -f /var/log/cybertv-backend.err.log

# Verificar se a porta 8001 está livre
lsof -i :8001

# Reinstalar dependências
cd /var/www/cybertv-suporte/backend
pip3 install -r requirements.txt
supervisorctl restart cybertv-backend
```

### Problema: Frontend não carrega

**Solução:**
```bash
# Verificar se o build existe
ls -la /var/www/cybertv-suporte/frontend/build

# Refazer build
cd /var/www/cybertv-suporte/frontend
yarn build

# Reiniciar Nginx
systemctl restart nginx
```

### Problema: MongoDB não conecta

**Solução:**
```bash
# Verificar status
systemctl status mongod

# Iniciar MongoDB
systemctl start mongod

# Ativar na inicialização
systemctl enable mongod

# Testar conexão
mongosh
```

## 📊 Monitoramento

### Uso de Recursos

```bash
# CPU e Memória
htop

# Espaço em disco
df -h

# Uso de porta
netstat -tulpn | grep LISTEN
```

### Logs de Acesso

```bash
# Ver últimos acessos
tail -f /var/log/nginx/access.log

# Contar requisições
cat /var/log/nginx/access.log | wc -l
```

## 🔄 Backup

### Backup do Banco de Dados

```bash
# Criar backup
mongodump --db cybertv_suporte --out /backups/$(date +%Y%m%d)

# Restaurar backup
mongorestore --db cybertv_suporte /backups/20250101/cybertv_suporte
```

### Backup Automático (Cron)

```bash
# Editar crontab
crontab -e

# Adicionar backup diário às 3h da manhã
0 3 * * * mongodump --db cybertv_suporte --out /backups/$(date +\%Y\%m\%d)
```

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs (comandos acima)
2. Reinicie os serviços
3. Verifique se o DNS está propagado
4. Verifique se as portas estão abertas no firewall

## 🎯 Arquitetura Final

```
┌─────────────────────────────────────────┐
│         att.suporte.help (Nginx)        │
│         + SSL (Let's Encrypt)           │
└────────────┬────────────────────────────┘
             │
       ┌─────┴─────┐
       │           │
   ┌───▼───┐  ┌───▼────┐
   │ React │  │ FastAPI│
   │ Build │  │  :8001 │
   │ (/)   │  │ (/api) │
   └───────┘  └────┬───┘
                   │
              ┌────▼─────┐
              │ MongoDB  │
              │   Local  │
              └──────────┘
```

---

**✅ Deploy Completo! Sua aplicação está no ar em https://att.suporte.help**
