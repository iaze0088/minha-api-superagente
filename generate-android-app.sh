#!/bin/bash

# ========================================
# Script de Geração Automática do App Android
# WA Suporte - Play Store Ready
# ========================================

echo "🚀 Iniciando geração do aplicativo WA Suporte para Android..."
echo ""

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não está instalado${NC}"
    echo "Instale Node.js em: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✅ Node.js instalado${NC}"

# Verificar se npm está instalado
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm não está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm instalado${NC}"

# Instalar Bubblewrap globalmente
echo ""
echo -e "${BLUE}📦 Instalando Bubblewrap CLI...${NC}"
npm install -g @bubblewrap/cli

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erro ao instalar Bubblewrap${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Bubblewrap instalado com sucesso${NC}"

# Criar diretório para o projeto Android
echo ""
echo -e "${BLUE}📁 Criando diretório do projeto...${NC}"
mkdir -p wa-suporte-android
cd wa-suporte-android

# Configuração do projeto
APP_NAME="WA Suporte"
PACKAGE_NAME="com.cybertv.wasuporte"
HOST_URL="https://reseller-sync.preview.emergentagent.com"
THEME_COLOR="#075e54"
BACKGROUND_COLOR="#075e54"

echo ""
echo -e "${BLUE}🔧 Configurações do App:${NC}"
echo "  Nome: $APP_NAME"
echo "  Package: $PACKAGE_NAME"
echo "  URL: $HOST_URL"
echo "  Cor: $THEME_COLOR"
echo ""

# Inicializar projeto Bubblewrap
echo -e "${BLUE}🔨 Inicializando projeto TWA...${NC}"
bubblewrap init \
  --manifest "$HOST_URL/manifest.json" \
  --name "$APP_NAME" \
  --packageId "$PACKAGE_NAME" \
  --host "$HOST_URL" \
  --startUrl "/" \
  --themeColor "$THEME_COLOR" \
  --backgroundColor "$BACKGROUND_COLOR" \
  --iconUrl "$HOST_URL/icon-512.png" \
  --maskableIconUrl "$HOST_URL/icon-512.png" \
  --shortcuts "$HOST_URL/manifest.json" \
  --monochromeIconUrl "$HOST_URL/icon-512.png"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erro ao inicializar projeto${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Projeto inicializado${NC}"

# Construir APK
echo ""
echo -e "${BLUE}🔨 Construindo APK de desenvolvimento...${NC}"
bubblewrap build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erro ao construir APK${NC}"
    exit 1
fi

echo -e "${GREEN}✅ APK construído com sucesso!${NC}"

# Instruções finais
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ App Android gerado com sucesso!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "📱 Arquivos gerados em: $(pwd)"
echo ""
echo "📦 Próximos passos:"
echo ""
echo "1️⃣  Para gerar APK de PRODUÇÃO (Play Store):"
echo "   bubblewrap build --release"
echo ""
echo "2️⃣  Para assinar o APK:"
echo "   jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \\"
echo "     -keystore wa-suporte.keystore app-release-unsigned.apk wa-suporte"
echo ""
echo "3️⃣  Para alinhar o APK:"
echo "   zipalign -v 4 app-release-unsigned.apk wa-suporte-release.apk"
echo ""
echo "4️⃣  Testar o APK em um dispositivo:"
echo "   adb install app-debug.apk"
echo ""
echo "📖 Guia completo: /app/PLAYSTORE_GUIDE.md"
echo ""
echo -e "${BLUE}🎉 Boa sorte com a publicação!${NC}"
