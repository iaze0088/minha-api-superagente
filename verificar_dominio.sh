#!/bin/bash

echo "🔍 Verificando configuração do domínio suporte.help"
echo "=================================================="
echo ""

# 1. Verificar resolução DNS
echo "1️⃣ Resolução DNS:"
nslookup suporte.help 2>/dev/null || echo "⚠️ Domínio ainda não resolvido"
echo ""

# 2. Testar conectividade
echo "2️⃣ Teste de conectividade:"
if ping -c 2 suporte.help >/dev/null 2>&1; then
    echo "✅ Domínio acessível"
else
    echo "❌ Domínio não acessível ainda"
fi
echo ""

# 3. Verificar HTTPS
echo "3️⃣ Teste HTTPS:"
if curl -s -o /dev/null -w "%{http_code}" https://suporte.help | grep -q "200\|301\|302"; then
    echo "✅ HTTPS funcionando"
else
    echo "⚠️ HTTPS ainda não configurado"
fi
echo ""

# 4. Verificar API
echo "4️⃣ Teste da API:"
if curl -s https://suporte.help/api/agents >/dev/null 2>&1; then
    echo "✅ API respondendo"
else
    echo "⚠️ API ainda não acessível"
fi
echo ""

# 5. Status dos serviços
echo "5️⃣ Status dos serviços:"
sudo supervisorctl status backend frontend
echo ""

# 6. Variável de ambiente
echo "6️⃣ Configuração backend:"
grep "REACT_APP_BACKEND_URL" /app/backend/.env
echo ""

echo "=================================================="
echo "✨ Verificação completa!"
echo ""
echo "🌐 Acesse:"
echo "   Cliente: https://suporte.help/"
echo "   Atendente: https://suporte.help/atendente/login"
echo "   Admin: https://suporte.help/admin/login"
