#!/bin/bash

# Script para verificar status de um ticket e testar IA

if [ -z "$1" ]; then
    echo "❌ Uso: ./verificar_ticket.sh <whatsapp_do_cliente>"
    echo "   Exemplo: ./verificar_ticket.sh 19989615252"
    exit 1
fi

WHATSAPP=$1

python3 << EOF
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client['support_chat']

# Buscar cliente
user = db.users.find_one({"whatsapp": "$WHATSAPP"})

if not user:
    print(f"❌ Cliente $WHATSAPP não encontrado")
    exit(1)

print(f"✅ CLIENTE ENCONTRADO:")
print(f"   WhatsApp: {user.get('whatsapp')}")
print(f"   ID: {user.get('id')}")
print(f"   Nome: {user.get('name', 'N/A')}")

# Buscar ticket
ticket = db.tickets.find_one({"client_id": user['id']})

if not ticket:
    print(f"\n❌ Ticket não encontrado para este cliente")
    exit(1)

print(f"\n📋 TICKET:")
print(f"   ID: {ticket['id']}")
print(f"   Department ID: {ticket.get('department_id', '❌ NENHUM - IA NÃO VAI RESPONDER!')}")
print(f"   Assigned Agent: {ticket.get('assigned_agent_id', '❌ NENHUM')}")
print(f"   Status: {ticket.get('status')}")
print(f"   AI Disabled: {ticket.get('ai_disabled_until', 'N/A')}")

# Verificar departamento
if ticket.get('department_id'):
    dept = db.departments.find_one({"id": ticket['department_id']})
    if dept:
        print(f"\n🏢 DEPARTAMENTO:")
        print(f"   Nome: {dept.get('name')}")
        print(f"   AI Agent ID: {dept.get('ai_agent_id', '❌ NENHUM')}")
        
        # Verificar agente IA
        if dept.get('ai_agent_id'):
            agent = db.ai_agents.find_one({"id": dept['ai_agent_id']})
            if agent:
                print(f"\n🤖 AGENTE IA:")
                print(f"   Nome: {agent.get('name')}")
                print(f"   Ativo: {'✅ Sim' if agent.get('is_active') else '❌ Não'}")
                print(f"   Modelo: {agent.get('llm_model')}")
                print(f"   Linked Agents: {agent.get('linked_agents', []) or '(Todos)'}")
            else:
                print(f"\n❌ Agente IA não encontrado!")
    else:
        print(f"\n❌ Departamento não encontrado!")
else:
    print(f"\n⚠️ PROBLEMA: Ticket sem departamento!")
    print(f"   SOLUÇÃO: Cliente deve selecionar departamento no chat")

# Últimas mensagens
messages = list(db.messages.find({"ticket_id": ticket['id']}).sort("created_at", -1).limit(5))
print(f"\n💬 ÚLTIMAS 5 MENSAGENS:")
for msg in reversed(messages):
    from_type = msg.get('from_type', 'N/A')
    text = msg.get('text', '')[:60]
    print(f"   [{from_type}]: {text}...")

print(f"\n{'='*80}")
print(f"✅ Para testar IA: Envie mensagem como cliente e monitore:")
print(f"   tail -f /var/log/ai_agent.log")
print(f"{'='*80}")
EOF
