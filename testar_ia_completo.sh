#!/bin/bash

echo "🤖 TESTE COMPLETO DO SISTEMA DE IA"
echo "="*80

# Limpar log
sudo truncate -s 0 /var/log/ai_agent.log

python3 << 'EOF'
import requests
import time
from pymongo import MongoClient

print("\n📋 PASSO 1: Configurando teste...")

# Conectar ao banco
client_db = MongoClient("mongodb://localhost:27017")
db = client_db['support_chat']

# Buscar um ticket com departamento SUPORTE
ticket = db.tickets.find_one({
    "department_id": "489e8c45-2d92-4d81-861a-f15e06d8a73d",
    "status": {"$in": ["EM_ESPERA", "ATENDENDO"]}
})

if not ticket:
    print("❌ Nenhum ticket com departamento SUPORTE encontrado!")
    print("💡 Crie um cliente primeiro via interface web")
    exit(1)

print(f"✅ Ticket encontrado: {ticket['id'][:20]}...")

# Buscar cliente
user = db.users.find_one({"id": ticket['client_id']})

if not user:
    print("❌ Cliente não encontrado!")
    exit(1)

print(f"✅ Cliente: WhatsApp {user.get('whatsapp')}")

# Fazer login
print("\n📋 PASSO 2: Fazendo login como cliente...")
login_resp = requests.post(
    "http://localhost:8001/api/auth/client/login",
    json={"whatsapp": user['whatsapp'], "pin": user.get('pin', '12')}
)

if login_resp.status_code != 200:
    print(f"❌ Erro no login: {login_resp.status_code}")
    exit(1)

token = login_resp.json()['token']
user_id = login_resp.json()['user_data']['id']
print("✅ Login realizado com sucesso")

# Buscar agentes
agents_resp = requests.get(
    "http://localhost:8001/api/agents",
    headers={"Authorization": f"Bearer {token}"}
)
agent_id = agents_resp.json()[0]['id']

# Enviar mensagem de teste
print("\n📋 PASSO 3: Enviando mensagem de teste...")
test_message = "Olá! Preciso de ajuda URGENTE com instalação"

msg_resp = requests.post(
    "http://localhost:8001/api/messages",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "from_type": "client",
        "from_id": user_id,
        "to_type": "agent",
        "to_id": agent_id,
        "kind": "text",
        "text": test_message
    }
)

if msg_resp.status_code != 200:
    print(f"❌ Erro ao enviar mensagem: {msg_resp.status_code}")
    print(msg_resp.json())
    exit(1)

print(f"✅ Mensagem enviada: '{test_message}'")
print("\n📋 PASSO 4: Aguardando resposta da IA...")
print("   (Delay configurado: 3 segundos + processamento LLM: ~2-3s)")

for i in range(7):
    time.sleep(1)
    print(f"   ⏳ {i+1}/7 segundos...")

print("\n📋 PASSO 5: Verificando se IA respondeu...")

# Buscar mensagens recentes
messages = list(db.messages.find({"ticket_id": ticket['id']}).sort("created_at", -1).limit(3))

ai_response_found = False
for msg in messages:
    if msg.get('from_type') == 'ai' and msg.get('created_at') > msg_resp.json().get('created_at', ''):
        ai_response_found = True
        print(f"\n✅ IA RESPONDEU COM SUCESSO!")
        print(f"📤 Resposta: {msg.get('text', '')[:150]}...")
        break

if not ai_response_found:
    print("\n❌ IA NÃO RESPONDEU!")
    print("💡 Verificando logs...")

print(f"\n📋 PASSO 6: Ticket ID para teste manual:")
print(f"   {ticket['id']}")
print(f"   WhatsApp: {user.get('whatsapp')}")
EOF

echo ""
echo "📋 LOGS DETALHADOS DA IA:"
echo "="*80
tail -n 100 /var/log/ai_agent.log

echo ""
echo "="*80
echo "✅ TESTE COMPLETO!"
echo "="*80
