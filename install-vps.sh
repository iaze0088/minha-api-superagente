#!/bin/bash

###############################################################################
# CYBERTV CHAT - Script de Instalação Automática para VPS
# Autor: Sistema Emergent AI
# Versão: 1.0
###############################################################################

set -e  # Parar em caso de erro

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          🚀 CYBERTV CHAT - INSTALAÇÃO AUTOMÁTICA          ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para printar mensagens coloridas
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    print_error "Por favor, execute como root (use: sudo bash install.sh)"
    exit 1
fi

print_info "Iniciando instalação..."
echo ""

###############################################################################
# PASSO 1: COLETAR INFORMAÇÕES
###############################################################################

echo "═══════════════════════════════════════════════════════════"
echo "PASSO 1: CONFIGURAÇÃO INICIAL"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Detectar IP da VPS
VPS_IP=$(curl -s ifconfig.me)
print_info "IP detectado da VPS: $VPS_IP"
echo ""

read -p "Digite seu domínio (ex: suporte.help) [ENTER para usar IP]: " DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN=$VPS_IP
    print_warning "Usando IP ao invés de domínio"
else
    print_success "Domínio configurado: $DOMAIN"
fi
echo ""

read -p "Digite a senha do Admin [ENTER para usar: 102030@ab]: " ADMIN_PASS
if [ -z "$ADMIN_PASS" ]; then
    ADMIN_PASS="102030@ab"
fi

# Gerar JWT Secret aleatório
JWT_SECRET=$(openssl rand -base64 32)
print_success "JWT Secret gerado automaticamente"
echo ""

###############################################################################
# PASSO 2: ATUALIZAR SISTEMA E INSTALAR DEPENDÊNCIAS
###############################################################################

echo "═══════════════════════════════════════════════════════════"
echo "PASSO 2: INSTALANDO DEPENDÊNCIAS"
echo "═══════════════════════════════════════════════════════════"
echo ""

print_info "Atualizando sistema..."
apt update -qq && apt upgrade -y -qq
print_success "Sistema atualizado"

print_info "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    print_success "Docker instalado"
else
    print_success "Docker já instalado"
fi

print_info "Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt install docker-compose -y -qq
    print_success "Docker Compose instalado"
else
    print_success "Docker Compose já instalado"
fi

print_info "Instalando Nginx..."
apt install nginx -y -qq
systemctl enable nginx
print_success "Nginx instalado"

print_info "Instalando Certbot (para SSL)..."
apt install certbot python3-certbot-nginx -y -qq
print_success "Certbot instalado"

###############################################################################
# PASSO 3: CRIAR ESTRUTURA DE DIRETÓRIOS
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PASSO 3: CRIANDO ESTRUTURA DE DIRETÓRIOS"
echo "═══════════════════════════════════════════════════════════"
echo ""

APP_DIR="/opt/cybertv-chat"
print_info "Criando diretórios em $APP_DIR..."

mkdir -p $APP_DIR
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend
mkdir -p $APP_DIR/uploads
mkdir -p $APP_DIR/mongo-data

print_success "Estrutura criada"

###############################################################################
# PASSO 4: CRIAR DOCKER COMPOSE
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PASSO 4: CONFIGURANDO DOCKER COMPOSE"
echo "═══════════════════════════════════════════════════════════"
echo ""

cat > $APP_DIR/docker-compose.yml << EOF
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: cybertv-mongodb
    restart: always
    volumes:
      - ./mongo-data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=chatdb
    networks:
      - cybertv-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: python:3.11-slim
    container_name: cybertv-backend
    restart: always
    working_dir: /app
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - ADMIN_PASSWORD=$ADMIN_PASS
      - JWT_SECRET=$JWT_SECRET
    command: >
      bash -c "
        pip install --no-cache-dir -r requirements.txt &&
        uvicorn server:app --host 0.0.0.0 --port 8001
      "
    ports:
      - "8001:8001"
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - cybertv-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/config"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: node:18-alpine
    container_name: cybertv-frontend
    restart: always
    working_dir: /app
    volumes:
      - ./frontend:/app
    environment:
      - REACT_APP_BACKEND_URL=http://$DOMAIN/api
      - NODE_ENV=production
    command: >
      sh -c "
        yarn install --production=false &&
        yarn build &&
        yarn global add serve &&
        serve -s build -l 3000
      "
    ports:
      - "3000:3000"
    networks:
      - cybertv-network

networks:
  cybertv-network:
    driver: bridge

volumes:
  mongo-data:
EOF

print_success "Docker Compose configurado"

###############################################################################
# PASSO 5: CONFIGURAR NGINX
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PASSO 5: CONFIGURANDO NGINX"
echo "═══════════════════════════════════════════════════════════"
echo ""

cat > /etc/nginx/sites-available/cybertv << EOF
upstream backend {
    server localhost:8001;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 100M;

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Uploads
    location /uploads/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Logs
    access_log /var/log/nginx/cybertv-access.log;
    error_log /var/log/nginx/cybertv-error.log;
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/cybertv /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
if nginx -t > /dev/null 2>&1; then
    systemctl reload nginx
    print_success "Nginx configurado e recarregado"
else
    print_error "Erro na configuração do Nginx"
    exit 1
fi

###############################################################################
# PASSO 6: CONFIGURAR FIREWALL
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PASSO 6: CONFIGURANDO FIREWALL"
echo "═══════════════════════════════════════════════════════════"
echo ""

if command -v ufw &> /dev/null; then
    print_info "Configurando UFW..."
    ufw --force enable
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    print_success "Firewall configurado"
else
    print_warning "UFW não encontrado, pulando configuração de firewall"
fi

###############################################################################
# PASSO 7: CRIAR SCRIPT DE UPLOAD
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "PASSO 7: CRIANDO SCRIPTS AUXILIARES"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Script para fazer upload do código
cat > /root/upload-code.sh << 'UPLOADSCRIPT'
#!/bin/bash
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          📤 UPLOAD DO CÓDIGO - CYBERTV CHAT               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "INSTRUÇÕES:"
echo "1. Do seu computador, execute:"
echo ""
echo "   # Upload Backend:"
echo "   scp -r /caminho/do/backend/* root@$(curl -s ifconfig.me):/opt/cybertv-chat/backend/"
echo ""
echo "   # Upload Frontend:"
echo "   scp -r /caminho/do/frontend/* root@$(curl -s ifconfig.me):/opt/cybertv-chat/frontend/"
echo ""
echo "2. Após o upload, execute: bash /root/start-app.sh"
echo ""
UPLOADSCRIPT

chmod +x /root/upload-code.sh

# Script para iniciar aplicação
cat > /root/start-app.sh << 'STARTSCRIPT'
#!/bin/bash
cd /opt/cybertv-chat

echo "🚀 Iniciando aplicação..."

# Parar containers anteriores
docker-compose down 2>/dev/null

# Iniciar containers
docker-compose up -d

echo ""
echo "⏳ Aguardando containers iniciarem (30 segundos)..."
sleep 30

echo ""
echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "✅ Aplicação iniciada!"
echo ""
echo "📝 Ver logs:"
echo "   docker-compose logs -f"
echo ""
STARTSCRIPT

chmod +x /root/start-app.sh

# Script para ver logs
cat > /root/logs.sh << 'LOGSCRIPT'
#!/bin/bash
cd /opt/cybertv-chat
docker-compose logs -f
LOGSCRIPT

chmod +x /root/logs.sh

# Script para reiniciar
cat > /root/restart-app.sh << 'RESTARTSCRIPT'
#!/bin/bash
cd /opt/cybertv-chat
echo "🔄 Reiniciando aplicação..."
docker-compose restart
echo "✅ Aplicação reiniciada!"
RESTARTSCRIPT

chmod +x /root/restart-app.sh

# Script para parar
cat > /root/stop-app.sh << 'STOPSCRIPT'
#!/bin/bash
cd /opt/cybertv-chat
echo "⏹️  Parando aplicação..."
docker-compose down
echo "✅ Aplicação parada!"
STOPSCRIPT

chmod +x /root/stop-app.sh

# Script para backup
cat > /root/backup.sh << 'BACKUPSCRIPT'
#!/bin/bash
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cybertv_backup_$TIMESTAMP.tar.gz"

echo "💾 Criando backup..."

cd /opt/cybertv-chat
docker-compose exec -T mongodb mongodump --archive=/data/db/backup.archive --gzip

tar -czf $BACKUP_FILE \
    backend/ \
    frontend/ \
    mongo-data/ \
    docker-compose.yml

echo "✅ Backup criado: $BACKUP_FILE"
BACKUPSCRIPT

chmod +x /root/backup.sh

print_success "Scripts auxiliares criados"

###############################################################################
# PASSO 8: CONFIGURAR SSL (se for domínio)
###############################################################################

if [ "$DOMAIN" != "$VPS_IP" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "PASSO 8: CONFIGURAR SSL (HTTPS)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    read -p "Deseja configurar SSL/HTTPS agora? (s/N): " SETUP_SSL
    if [[ $SETUP_SSL =~ ^[Ss]$ ]]; then
        read -p "Digite seu email para o Let's Encrypt: " LETSENCRYPT_EMAIL
        
        print_info "Obtendo certificado SSL..."
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $LETSENCRYPT_EMAIL
        
        if [ $? -eq 0 ]; then
            print_success "SSL configurado com sucesso!"
            
            # Configurar renovação automática
            echo "0 0,12 * * * root certbot renew --quiet" >> /etc/crontab
            print_success "Renovação automática de SSL configurada"
        else
            print_warning "Não foi possível configurar SSL. Você pode tentar manualmente depois."
        fi
    else
        print_info "SSL não configurado. Você pode configurar depois com: certbot --nginx -d $DOMAIN"
    fi
fi

###############################################################################
# FINALIZAÇÃO
###############################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

print_success "Sistema instalado em: $APP_DIR"
echo ""

echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  FAZER UPLOAD DO CÓDIGO:"
echo "    Do seu computador, execute:"
echo ""
echo "    scp -r /caminho/backend/* root@$VPS_IP:/opt/cybertv-chat/backend/"
echo "    scp -r /caminho/frontend/* root@$VPS_IP:/opt/cybertv-chat/frontend/"
echo ""
echo "    OU execute: bash /root/upload-code.sh (para ver instruções)"
echo ""
echo "2️⃣  INICIAR APLICAÇÃO:"
echo "    bash /root/start-app.sh"
echo ""
echo "3️⃣  ACESSAR:"
if [ "$DOMAIN" != "$VPS_IP" ]; then
    echo "    http://$DOMAIN"
    if [[ $SETUP_SSL =~ ^[Ss]$ ]]; then
        echo "    https://$DOMAIN"
    fi
else
    echo "    http://$VPS_IP"
fi
echo ""

echo "📚 COMANDOS ÚTEIS:"
echo "    bash /root/start-app.sh      # Iniciar aplicação"
echo "    bash /root/stop-app.sh       # Parar aplicação"
echo "    bash /root/restart-app.sh    # Reiniciar aplicação"
echo "    bash /root/logs.sh           # Ver logs"
echo "    bash /root/backup.sh         # Fazer backup"
echo ""

echo "🔑 CREDENCIAIS:"
echo "    Admin: $DOMAIN/admin"
echo "    Senha: $ADMIN_PASS"
echo ""

echo "💾 ARQUIVOS DE CONFIGURAÇÃO:"
echo "    Docker Compose: $APP_DIR/docker-compose.yml"
echo "    Nginx: /etc/nginx/sites-available/cybertv"
echo "    Scripts: /root/*.sh"
echo ""

print_warning "IMPORTANTE: Não esqueça de fazer upload do código antes de iniciar!"
echo ""

# Salvar informações em arquivo
cat > /root/cybertv-info.txt << EOF
═══════════════════════════════════════════════════════════
CYBERTV CHAT - INFORMAÇÕES DA INSTALAÇÃO
═══════════════════════════════════════════════════════════

Data de Instalação: $(date)
IP da VPS: $VPS_IP
Domínio: $DOMAIN
Senha Admin: $ADMIN_PASS
JWT Secret: $JWT_SECRET

Diretório da Aplicação: $APP_DIR

URLs:
- Frontend: http://$DOMAIN
- Admin: http://$DOMAIN/admin
- API: http://$DOMAIN/api
- WebSocket: ws://$DOMAIN/ws

Scripts Úteis:
- /root/start-app.sh      # Iniciar
- /root/stop-app.sh       # Parar
- /root/restart-app.sh    # Reiniciar
- /root/logs.sh           # Ver logs
- /root/backup.sh         # Backup
- /root/upload-code.sh    # Instruções de upload

Comandos Docker:
cd $APP_DIR
docker-compose ps              # Ver status
docker-compose logs -f         # Ver logs
docker-compose restart         # Reiniciar
docker-compose down            # Parar
docker-compose up -d           # Iniciar

═══════════════════════════════════════════════════════════
EOF

print_success "Informações salvas em: /root/cybertv-info.txt"
echo ""
print_info "Para ver essas informações novamente: cat /root/cybertv-info.txt"
echo ""
