#!/bin/bash

#########################################################
# Script de Deploy Automatizado - CYBERTV Suporte
# Domínio: att.suporte.help
# IP: 157.180.19.132
#########################################################

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  CYBERTV Suporte - Deploy Automático  ${NC}"
echo -e "${GREEN}========================================${NC}"

# Configurações
DOMAIN="att.suporte.help"
APP_DIR="/var/www/cybertv-suporte"
EMAIL="admin@suporte.help"  # Para Let's Encrypt
ADMIN_PASSWORD="admin123"  # Senha padrão do admin
JWT_SECRET=$(openssl rand -hex 32)

echo -e "${YELLOW}[1/12] Atualizando sistema...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${YELLOW}[2/12] Instalando dependências básicas...${NC}"
apt-get install -y curl wget git build-essential software-properties-common

echo -e "${YELLOW}[3/12] Instalando Node.js 18.x...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

echo -e "${YELLOW}[4/12] Instalando Yarn...${NC}"
npm install -g yarn

echo -e "${YELLOW}[5/12] Instalando Python 3.10+...${NC}"
apt-get install -y python3 python3-pip python3-venv

echo -e "${YELLOW}[6/12] Instalando MongoDB...${NC}"
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
apt-get update
apt-get install -y mongodb-org

# Iniciar MongoDB
systemctl start mongod
systemctl enable mongod

echo -e "${YELLOW}[7/12] Instalando Nginx...${NC}"
apt-get install -y nginx

echo -e "${YELLOW}[8/12] Instalando Certbot para SSL...${NC}"
apt-get install -y certbot python3-certbot-nginx

echo -e "${YELLOW}[9/12] Instalando Supervisor...${NC}"
apt-get install -y supervisor

echo -e "${YELLOW}[10/12] Configurando aplicação...${NC}"

# Criar diretório da aplicação
mkdir -p $APP_DIR
cd $APP_DIR

# Se o código já existe localmente, copiar
if [ -d "/app/backend" ] && [ -d "/app/frontend" ]; then
    echo -e "${GREEN}Copiando código da aplicação...${NC}"
    cp -r /app/backend $APP_DIR/
    cp -r /app/frontend $APP_DIR/
else
    echo -e "${RED}ERRO: Diretórios /app/backend e /app/frontend não encontrados!${NC}"
    exit 1
fi

# Configurar backend
echo -e "${GREEN}Configurando Backend...${NC}"
cd $APP_DIR/backend

# Criar .env do backend
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017/cybertv_suporte
ADMIN_PASSWORD=$ADMIN_PASSWORD
JWT_SECRET=$JWT_SECRET
EOF

# Instalar dependências Python
pip3 install -r requirements.txt

# Configurar frontend
echo -e "${GREEN}Configurando Frontend...${NC}"
cd $APP_DIR/frontend

# Criar .env do frontend
cat > .env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

# Instalar dependências Node
yarn install

# Build do frontend
echo -e "${GREEN}Buildando Frontend...${NC}"
yarn build

echo -e "${YELLOW}[11/12] Configurando Nginx...${NC}"

# Criar configuração do Nginx
cat > /etc/nginx/sites-available/cybertv << 'EOF'
server {
    listen 80;
    server_name att.suporte.help;

    client_max_body_size 100M;

    # Frontend (React build)
    location / {
        root /var/www/cybertv-suporte/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/cybertv /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração do Nginx
nginx -t

# Reiniciar Nginx
systemctl restart nginx

echo -e "${YELLOW}Configurando SSL com Let's Encrypt...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

echo -e "${YELLOW}[12/12] Configurando Supervisor...${NC}"

# Configurar Supervisor para Backend
cat > /etc/supervisor/conf.d/cybertv-backend.conf << EOF
[program:cybertv-backend]
command=python3 -m uvicorn server:app --host 0.0.0.0 --port 8001
directory=$APP_DIR/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/cybertv-backend.err.log
stdout_logfile=/var/log/cybertv-backend.out.log
user=root
environment=PYTHONUNBUFFERED=1
EOF

# Recarregar Supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart cybertv-backend

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploy Concluído com Sucesso! 🚀    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "${GREEN}✅ Domínio:${NC} https://$DOMAIN"
echo -e "${GREEN}✅ Backend:${NC} Rodando na porta 8001"
echo -e "${GREEN}✅ Frontend:${NC} Build servido pelo Nginx"
echo -e "${GREEN}✅ MongoDB:${NC} Rodando localmente"
echo -e "${GREEN}✅ SSL:${NC} Certificado Let's Encrypt configurado"
echo -e ""
echo -e "${YELLOW}Credenciais de Admin:${NC}"
echo -e "  Email: admin@admin.com"
echo -e "  Senha: $ADMIN_PASSWORD"
echo -e ""
echo -e "${YELLOW}Comandos Úteis:${NC}"
echo -e "  - Ver logs backend: tail -f /var/log/cybertv-backend.out.log"
echo -e "  - Reiniciar backend: supervisorctl restart cybertv-backend"
echo -e "  - Status serviços: supervisorctl status"
echo -e "  - Reiniciar Nginx: systemctl restart nginx"
echo -e ""
echo -e "${GREEN}Acesse: https://$DOMAIN${NC}"
echo -e "${GREEN}========================================${NC}"
