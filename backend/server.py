from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Set
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import aiofiles
from models import *
from tenant_middleware import detect_tenant, get_current_tenant, apply_tenant_filter, TenantContext, tenant_context as global_tenant_context
from ai_service import ai_service
import mimetypes
import re

# Logger dedicado para IA (compartilhado com ai_service.py)
ai_logger = logging.getLogger("ai_agent")
ai_logger.setLevel(logging.INFO)

# Se não tiver handlers ainda, adicionar
if not ai_logger.handlers:
    file_handler = logging.FileHandler("/var/log/ai_agent.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    ai_logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    ai_logger.addHandler(console_handler)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'support_chat')]

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'sua-chave-secreta-super-segura-aqui')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Inicia background tasks ao iniciar o servidor"""
    asyncio.create_task(check_department_timeouts())
    asyncio.create_task(reactivate_ai_after_timeout())
    print("✅ Background tasks iniciadas: timeout de departamentos e reativação de IA")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        await websocket.accept()
        
        # Se já existe outra sessão, desconectar a antiga
        if user_id in self.user_sessions and self.user_sessions[user_id] != session_id:
            await self.disconnect_user(user_id)
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_sessions[user_id] = session_id
    
    async def disconnect_user(self, user_id: str):
        if user_id in self.active_connections:
            for conn in list(self.active_connections[user_id]):
                try:
                    await conn.send_json({"type": "force_logout", "reason": "Nova sessão iniciada"})
                    await conn.close()
                except:
                    pass
            del self.active_connections[user_id]
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        print(f"📤 [send_to_user] Tentando enviar para user_id: {user_id}")
        print(f"   Active connections: {list(self.active_connections.keys())}")
        
        if user_id in self.active_connections:
            print(f"   ✅ User encontrado! Conexões ativas: {len(self.active_connections[user_id])}")
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                    print(f"   ✅ Mensagem enviada com sucesso via WebSocket para {user_id}")
                except Exception as e:
                    print(f"   ❌ ERRO ao enviar via WebSocket para {user_id}: {e}")
        else:
            print(f"   ⚠️ User {user_id} NÃO está em active_connections!")
    
    async def broadcast_to_agents(self, message: dict):
        agents = await db.agents.find({}, {"id": 1}).to_list(None)
        for agent in agents:
            await self.send_to_user(agent["id"], message)

manager = ConnectionManager()

# Helper para enviar mensagem de seleção de departamento
async def send_department_selection(ticket_id: str, client_id: str, reseller_id: Optional[str] = None):
    """Envia mensagem automática pedindo ao cliente para escolher um departamento"""
    # Buscar departamentos disponíveis
    query = {}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    departments = await db.departments.find(query).to_list(None)
    
    if not departments or len(departments) == 0:
        # Sem departamentos configurados, não envia nada
        return
    
    # Criar mensagem com botões
    buttons = []
    for dept in departments:
        buttons.append({
            "id": dept["id"],
            "label": dept["name"],
            "description": dept.get("description", "")
        })
    
    # Criar mensagem no banco
    message = {
        "id": str(uuid.uuid4()),
        "ticket_id": ticket_id,
        "from_type": "system",
        "kind": "department_selection",
        "text": "Você deseja o atendimento para qual área? Clique em uma das opções abaixo:",
        "buttons": buttons,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reseller_id": reseller_id
    }
    
    await db.messages.insert_one(message)
    
    # Enviar via WebSocket para o cliente
    await manager.send_to_user(client_id, {
        "type": "new_message",
        "message": message
    })
    
    # Marcar timestamp de quando enviou
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"department_choice_sent_at": datetime.now(timezone.utc).isoformat()}}
    )

async def process_message_with_ai(ticket: Dict, message_text: str, reseller_id: str):
    """Processa mensagem e gera resposta da IA se houver agente vinculado"""
    ai_logger.info("🟢 " + "="*80)
    ai_logger.info(f"🔍 NOVA MENSAGEM RECEBIDA PARA PROCESSAMENTO IA")
    ai_logger.info(f"📋 Ticket ID: {ticket.get('id')}")
    ai_logger.info(f"👤 Cliente: {ticket.get('client_name', 'N/A')}")
    ai_logger.info(f"🏢 Reseller ID: {reseller_id}")
    ai_logger.info(f"💬 Mensagem: {message_text[:100]}...")
    
    try:
        # Verificar se IA foi desativada manualmente
        ai_disabled_until = ticket.get("ai_disabled_until")
        if ai_disabled_until:
            try:
                disabled_until = datetime.fromisoformat(ai_disabled_until)
                if datetime.now(timezone.utc) < disabled_until:
                    ai_logger.info(f"❌ IA DESATIVADA MANUALMENTE para ticket {ticket['id']} até {disabled_until}")
                    ai_logger.info("🔴 " + "="*80)
                    return
                else:
                    ai_logger.info(f"✅ Tempo de desativação expirou, IA pode responder novamente")
            except Exception as e:
                ai_logger.warning(f"⚠️ Erro ao verificar ai_disabled_until: {e}")
        
        # Verificar se o ticket tem departamento
        department_id = ticket.get("department_id")
        ai_logger.info(f"📂 Verificando departamento...")
        ai_logger.info(f"   Department ID: {department_id}")
        
        if not department_id:
            ai_logger.info(f"❌ BLOQUEIO: Ticket {ticket['id']} sem departamento atribuído")
            ai_logger.info(f"💡 Ação necessária: Cliente deve selecionar um departamento")
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Buscar departamento
        ai_logger.info(f"🔎 Buscando departamento no banco de dados...")
        department = await db.departments.find_one({"id": department_id, "reseller_id": reseller_id})
        
        if not department:
            ai_logger.error(f"💥 ERRO: Departamento {department_id} não encontrado no banco!")
            ai_logger.info("🔴 " + "="*80)
            return
        
        ai_logger.info(f"✅ Departamento encontrado:")
        ai_logger.info(f"   Nome: {department.get('name')}")
        ai_logger.info(f"   AI Agent ID: {department.get('ai_agent_id', 'NENHUM')}")
        
        if not department.get("ai_agent_id"):
            ai_logger.info(f"❌ BLOQUEIO: Departamento '{department.get('name')}' sem IA vinculada")
            ai_logger.info(f"💡 Ação necessária: Vincular um agente IA ao departamento")
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Buscar agente IA
        ai_logger.info(f"🔎 Buscando agente IA no banco de dados...")
        ai_agent = await db.ai_agents.find_one({
            "id": department["ai_agent_id"],
            "reseller_id": reseller_id,
            "is_active": True
        })
        
        if not ai_agent:
            ai_logger.error(f"💥 ERRO: Agente IA {department['ai_agent_id']} não encontrado ou inativo!")
            ai_logger.info(f"💡 Ação necessária: Verificar se agente IA existe e está ativo")
            ai_logger.info("🔴 " + "="*80)
            return
        
        ai_logger.info(f"✅ Agente IA encontrado:")
        ai_logger.info(f"   Nome: {ai_agent.get('name')}")
        ai_logger.info(f"   ID: {ai_agent.get('id')}")
        ai_logger.info(f"   Ativo: {ai_agent.get('is_active')}")
        ai_logger.info(f"   Modelo: {ai_agent.get('llm_provider', 'N/A')}/{ai_agent.get('llm_model', 'N/A')}")
        
        # REMOVIDO: Verificação de linked_agents e assigned_agent_id
        # IA responde SEMPRE que o departamento tem IA configurada e ativa
        
        ai_logger.info(f"🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
        ai_logger.info(f"🤖 IA '{ai_agent.get('name', 'Sem nome')}' vai processar QUALQUER mensagem do cliente")
        
        # Buscar histórico de mensagens do ticket (LIMITADO a últimas 10 para evitar Context Window Exceeded)
        ai_logger.info(f"📚 Carregando histórico de mensagens (últimas 10)...")
        all_messages = await db.messages.find({"ticket_id": ticket["id"]}).sort("created_at", -1).limit(10).to_list(10)
        # Reverter ordem (mais antigas primeiro)
        messages = list(reversed(all_messages))
        ai_logger.info(f"   {len(messages)} mensagens carregadas")
        
        # Truncar mensagens muito longas para economizar tokens
        for msg in messages:
            if msg.get("text") and len(msg["text"]) > 500:
                original_len = len(msg["text"])
                msg["text"] = msg["text"][:500] + "..."
                ai_logger.info(f"   ⚠️ Mensagem truncada: {original_len} → 500 caracteres")
        
        # Buscar dados do cliente (para credenciais se permitido)
        ai_logger.info(f"👤 Buscando dados do cliente...")
        client = await db.users.find_one({"id": ticket["client_id"], "reseller_id": reseller_id})
        client_data = {
            "pinned_user": client.get("pinned_user") if client else None,
            "pinned_pass": client.get("pinned_pass") if client else None
        }
        ai_logger.info(f"   Cliente: {client.get('name', 'N/A') if client else 'N/A'}")
        ai_logger.info(f"   Credenciais disponíveis: {bool(client_data['pinned_user'] or client_data['pinned_pass'])}")
        
        # Gerar resposta da IA
        ai_logger.info(f"🚀 Chamando serviço de IA para gerar resposta...")
        ai_response = await ai_service.generate_response(
            agent_config=ai_agent,
            message=message_text,
            conversation_history=messages,
            client_data=client_data
        )
        
        if not ai_response:
            ai_logger.error("💥 ERRO: IA não gerou resposta (retornou None)")
            ai_logger.error("💡 Verificar logs acima para detalhes do erro")
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Aguardar tempo de resposta para humanização (response_delay_seconds)
        delay_seconds = ai_agent.get("response_delay_seconds", 3)
        if delay_seconds > 0:
            ai_logger.info(f"⏱️ Aguardando {delay_seconds} segundos para humanizar resposta...")
            await asyncio.sleep(delay_seconds)
        
        # Criar mensagem de resposta da IA
        ai_logger.info(f"💾 Salvando resposta da IA no banco de dados...")
        ai_message = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket["id"],
            "from_type": "ai",
            "from_name": ai_agent.get("name", "Assistente IA"),
            "text": ai_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reseller_id": reseller_id
        }
        
        await db.messages.insert_one(ai_message)
        ai_logger.info(f"✅ Mensagem da IA salva com sucesso (ID: {ai_message['id']})")
        
        # Atualizar última mensagem do ticket
        await db.tickets.update_one(
            {"id": ticket["id"]},
            {"$set": {
                "last_message": {
                    "text": ai_response[:100],
                    "from_type": "ai",
                    "created_at": ai_message["created_at"]
                },
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        ai_logger.info(f"✅ Ticket atualizado com última mensagem da IA")
        ai_logger.info(f"🎉 PROCESSO COMPLETO! IA respondeu com sucesso")
        ai_logger.info("🟢 " + "="*80)
        
        # Enviar via WebSocket para cliente e atendentes
        ai_logger.info(f"📡 Enviando mensagem via WebSocket...")
        ai_logger.info(f"   Cliente ID: {ticket['client_id']}")
        
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": ai_message
        })
        ai_logger.info(f"   ✅ Enviado para cliente")
        
        # Enviar para atendentes do departamento
        agents_in_dept = await db.agents.find({
            "reseller_id": reseller_id,
            "departments": department_id
        }).to_list(None)
        
        ai_logger.info(f"   👥 Atendentes no departamento: {len(agents_in_dept)}")
        
        for agent in agents_in_dept:
            await manager.send_to_user(agent["id"], {
                "type": "new_message",
                "message": ai_message
            })
            ai_logger.info(f"   ✅ Enviado para atendente: {agent.get('name', agent['id'][:10])}")
        
        ai_logger.info(f"📡 Todas mensagens WebSocket enviadas com sucesso!")
        ai_logger.info(f"✅ IA respondeu no ticket {ticket['id']}")
        
    except Exception as e:
        ai_logger.error("💥 " + "="*80)
        ai_logger.error(f"💥 ERRO CRÍTICO ao processar mensagem com IA!")
        ai_logger.error(f"   Tipo: {type(e).__name__}")
        ai_logger.error(f"   Mensagem: {str(e)}")
        import traceback
        ai_logger.error(f"   Traceback:\n{traceback.format_exc()}")
        ai_logger.error("💥 " + "="*80)

# Background task para verificar timeouts
async def check_department_timeouts():
    """Verifica tickets aguardando escolha de departamento e aplica timeout"""
    while True:
        try:
            await asyncio.sleep(30)  # Verificar a cada 30 segundos
            
            # Buscar tickets aguardando escolha de departamento
            tickets = await db.tickets.find({
                "awaiting_department_choice": True,
                "department_choice_sent_at": {"$exists": True, "$ne": None}
            }).to_list(None)
            
            now = datetime.now(timezone.utc)
            
            for ticket in tickets:
                sent_at = datetime.fromisoformat(ticket["department_choice_sent_at"])
                elapsed = (now - sent_at).total_seconds()
                
                # Buscar timeout do departamento padrão ou usar 120s
                default_dept = await db.departments.find_one({
                    "is_default": True,
                    "reseller_id": ticket.get("reseller_id")
                })
                
                timeout = default_dept.get("timeout_seconds", 120) if default_dept else 120
                
                if elapsed >= timeout:
                    # Timeout! Mover para departamento padrão
                    if default_dept:
                        await db.tickets.update_one(
                            {"id": ticket["id"]},
                            {"$set": {
                                "department_id": default_dept["id"],
                                "awaiting_department_choice": False,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        # Enviar mensagem de notificação
                        message = {
                            "id": str(uuid.uuid4()),
                            "ticket_id": ticket["id"],
                            "from_type": "system",
                            "kind": "text",
                            "text": f"⏱️ Tempo esgotado. Você foi direcionado automaticamente para: {default_dept['name']}",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "reseller_id": ticket.get("reseller_id")
                        }
                        
                        await db.messages.insert_one(message)
                        
                        # Enviar via WebSocket
                        await manager.send_to_user(ticket["client_id"], {
                            "type": "new_message",
                            "message": message
                        })
        except Exception as e:
            print(f"Error in timeout checker: {e}")

async def reactivate_ai_after_timeout():
    """Verifica tickets com IA desativada e reativa após 1 hora"""
    while True:
        try:
            await asyncio.sleep(60)  # Verificar a cada 60 segundos
            
            # Buscar tickets com IA desativada
            tickets = await db.tickets.find({
                "ai_disabled_until": {"$exists": True, "$ne": None}
            }).to_list(None)
            
            now = datetime.now(timezone.utc)
            
            for ticket in tickets:
                try:
                    disabled_until = datetime.fromisoformat(ticket["ai_disabled_until"])
                    
                    if now >= disabled_until:
                        # Tempo expirou, reativar IA
                        await db.tickets.update_one(
                            {"id": ticket["id"]},
                            {
                                "$unset": {"ai_disabled_until": "", "ai_disabled_by": ""},
                                "$set": {"updated_at": now.isoformat()}
                            }
                        )
                        
                        logger.info(f"✅ IA reativada automaticamente para ticket {ticket['id']}")
                        
                        # Opcional: Enviar mensagem ao atendente informando
                        # (não enviar ao cliente para não poluir conversa)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar ticket {ticket.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro na task de reativação de IA: {e}")



# Tenant helper
def get_request_tenant(request: Request) -> TenantContext:
    """Obtém o tenant context do request"""
    return getattr(request.state, "tenant", TenantContext())

# Auth helpers
def create_token(user_id: str, user_type: str, reseller_id: Optional[str] = None) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "reseller_id": reseller_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=365)  # Token válido por 1 ano
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirado - não deve acontecer com 365 dias
        logger.error("Token expirado (não deveria acontecer)")
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        # Token inválido
        logger.error(f"Token inválido: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        # Outro erro
        logger.error(f"Erro ao verificar token: {str(e)}")
        raise HTTPException(status_code=401, detail="Erro ao verificar token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

# Validation helpers
def validate_user_password_format(text: str) -> bool:
    """Valida se texto está no formato permitido de usuário/senha"""
    patterns = [
        r'^usuario:\s*.+\s*senha:\s*.+$',
        r'^Usuario:\s*.+\s*Senha:\s*.+$',
        r'^Usuário:\s*.+\s*Senha:\s*.+$',
        r'^USUÁRIO:\s*.+\s*SENHA:\s*.+$'
    ]
    text_normalized = ' '.join(text.split())
    return any(re.match(pattern, text_normalized, re.IGNORECASE | re.MULTILINE) for pattern in patterns)

def has_user_password_keywords(text: str) -> bool:
    """Verifica se tem palavras-chave de usuário/senha"""
    keywords = ['usuario', 'usuário', 'senha', 'password', 'user']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

async def validate_sensitive_data(text: str, config: dict) -> Optional[str]:
    """Valida dados sensíveis baseado na config permitida"""
    text_lower = text.lower()
    allowed_data = config.get('allowed_data', {})
    
    # Se tem usuário/senha, validar formato
    if has_user_password_keywords(text):
        if not validate_user_password_format(text):
            return "❌ Formato de usuário/senha inválido. Use: 'usuario: XXXX senha: XXXX'"
    
    # CPF check
    cpf_match = re.search(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', text)
    if cpf_match:
        cpf_found = cpf_match.group()
        allowed_cpfs = allowed_data.get('cpfs', [])
        if cpf_found not in allowed_cpfs:
            return "❌ CPF não autorizado. Cadastre no Admin primeiro."
    
    # Email check
    email_match = re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, re.IGNORECASE)
    if email_match:
        email_found = email_match.group()
        allowed_emails = allowed_data.get('emails', [])
        if email_found.lower() not in [e.lower() for e in allowed_emails]:
            return "❌ Email não autorizado. Cadastre no Admin primeiro."
    
    # Phone/WhatsApp check
    phone_match = re.search(r'\b(\+?55)?\D*\(?\d{2}\)?\D*\d{4,5}\D*\d{4}\b', text)
    if phone_match:
        phone_found = re.sub(r'\D', '', phone_match.group())
        allowed_phones = [re.sub(r'\D', '', p) for p in allowed_data.get('phones', [])]
        if phone_found not in allowed_phones:
            return "❌ Número de telefone não autorizado. Cadastre no Admin primeiro."
    
    # Random key check (chave aleatória PIX)
    if 'chave' in text_lower or 'pix' in text_lower:
        # Check se tem UUID ou chave aleatória
        random_key_match = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', text, re.IGNORECASE)
        if random_key_match:
            key_found = random_key_match.group()
            allowed_keys = allowed_data.get('random_keys', [])
            if key_found not in allowed_keys:
                return "❌ Chave aleatória não autorizada. Cadastre no Admin primeiro."
    
    return None

# Auth routes
@api_router.post("/auth/admin/login")
async def admin_login(data: AdminLogin):
    if data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    token = create_token("admin", "admin")
    return TokenResponse(token=token, user_type="admin", user_data={"id": "admin"})

@api_router.post("/auth/agent/login")
async def agent_login(data: AgentLogin, request: Request):
    # Buscar agente - primeiro tenta sem filtro de tenant
    agent = await db.agents.find_one({"login": data.login})
    
    if not agent or not bcrypt.checkpw(data.password.encode(), agent["pass_hash"].encode()):
        raise HTTPException(status_code=401, detail="Login ou senha inválidos")
    
    if not agent.get("is_active", True):
        raise HTTPException(status_code=403, detail="Conta desativada")
    
    token = create_token(agent["id"], "agent", agent.get("reseller_id"))
    return TokenResponse(token=token, user_type="agent", user_data={
        "id": agent["id"],
        "name": agent["name"],
        "avatar": agent.get("custom_avatar") or agent.get("avatar", "")
    }, reseller_id=agent.get("reseller_id"))

@api_router.post("/auth/client/login")
async def client_login(data: UserLogin, request: Request):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id
    
    # Buscar usuário com filtro de tenant
    query = {"whatsapp": data.whatsapp}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    user = await db.users.find_one(query)
    
    if not user:
        # First time - create user
        if len(data.pin) != 2 or not data.pin.isdigit():
            raise HTTPException(status_code=400, detail="PIN deve ter 2 dígitos")
        
        user_id = str(uuid.uuid4())
        pin_hash = bcrypt.hashpw(data.pin.encode(), bcrypt.gensalt()).decode()
        new_user = {
            "id": user_id,
            "whatsapp": data.whatsapp,
            "pin_hash": pin_hash,
            "display_name": "",
            "avatar": "",
            "custom_avatar": "",
            "gender": "",
            "pinned_user": "",
            "pinned_pass": "",
            "reseller_id": reseller_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
        user = new_user
    else:
        # Existing user
        if user.get("pin_hash"):
            if not bcrypt.checkpw(data.pin.encode(), user["pin_hash"].encode()):
                raise HTTPException(status_code=401, detail="PIN incorreto")
        else:
            # Set PIN
            if len(data.pin) != 2 or not data.pin.isdigit():
                raise HTTPException(status_code=400, detail="Crie PIN com 2 dígitos")
            pin_hash = bcrypt.hashpw(data.pin.encode(), bcrypt.gensalt()).decode()
            await db.users.update_one({"id": user["id"]}, {"$set": {"pin_hash": pin_hash}})
            user["pin_hash"] = pin_hash
    
    token = create_token(user["id"], "client", reseller_id)
    return TokenResponse(token=token, user_type="client", user_data={
        "id": user["id"],
        "whatsapp": user["whatsapp"],
        "display_name": user.get("display_name", ""),
        "avatar": user.get("custom_avatar") or user.get("avatar", ""),
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }, reseller_id=reseller_id)

# User routes
@api_router.get("/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {
        "id": user["id"],
        "whatsapp": user["whatsapp"],
        "display_name": user.get("display_name", ""),
        "avatar": user.get("custom_avatar") or user.get("avatar", ""),
        "gender": user.get("gender", ""),
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }

@api_router.put("/users/me")
async def update_user(data: dict, current_user: dict = Depends(get_current_user)):
    update_data = {}
    if "display_name" in data:
        update_data["display_name"] = data["display_name"]
    if "avatar" in data:
        update_data["avatar"] = data["avatar"]
    if "custom_avatar" in data:
        update_data["custom_avatar"] = data["custom_avatar"]
    if "gender" in data:
        update_data["gender"] = data["gender"]
    
    if update_data:
        await db.users.update_one({"id": current_user["user_id"]}, {"$set": update_data})
    return {"ok": True}

@api_router.put("/users/me/pin")
async def update_user_pin(data: dict, current_user: dict = Depends(get_current_user)):
    """Atualiza o PIN do usuário atual"""
    pin = data.get("pin", "")
    if not pin or len(pin) != 2 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve ter exatamente 2 dígitos")
    
    pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": {"pin_hash": pin_hash}})
    return {"ok": True}

@api_router.get("/users/whatsapp-popup-status")
async def check_whatsapp_popup_status(current_user: dict = Depends(get_current_user)):
    """Verifica se deve mostrar o pop-up de confirmação de WhatsApp"""
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        return {"should_show": False}
    
    # Verificar se já perguntou na última semana (7 dias)
    asked_at = user.get("whatsapp_asked_at")
    if asked_at:
        try:
            asked_date = datetime.fromisoformat(asked_at)
            days_since_asked = (datetime.now(timezone.utc) - asked_date).days
            if days_since_asked < 7:
                return {"should_show": False, "days_until_next": 7 - days_since_asked}
        except:
            pass
    
    # Se nunca perguntou ou passou 1 semana, mostrar popup
    return {"should_show": True}

@api_router.put("/users/me/whatsapp-confirm")
async def confirm_whatsapp(data: dict, current_user: dict = Depends(get_current_user)):
    """Confirma o WhatsApp do usuário atual"""
    whatsapp = data.get("whatsapp", "")
    
    await db.users.update_one(
        {"id": current_user["user_id"]},
        {"$set": {
            "whatsapp_confirmed": whatsapp,
            "whatsapp_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True}

@api_router.put("/users/me/pin")
async def update_pin(data: dict, current_user: dict = Depends(get_current_user)):
    pin = data.get("pin", "")
    if len(pin) != 2 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve ter 2 dígitos")
    
    pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": {"pin_hash": pin_hash}})
    return {"ok": True}

@api_router.get("/users/name-popup-status")
async def check_name_popup_status(current_user: dict = Depends(get_current_user)):
    """Verifica se deve mostrar o pop-up de nome (após primeira mensagem)"""
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        return {"should_show": False}
    
    # Se já tem nome cadastrado, não mostrar
    if user.get("display_name") and user.get("display_name").strip():
        return {"should_show": False, "has_name": True}
    
    # Se nunca perguntou, mostrar
    if not user.get("name_asked_at"):
        return {"should_show": True, "has_name": False}
    
    return {"should_show": False, "has_name": False}

@api_router.put("/users/me/name")
async def update_user_name(data: dict, current_user: dict = Depends(get_current_user)):
    """Atualiza o nome do usuário"""
    name = data.get("name", "").strip()
    
    # Validação: apenas nomes válidos (letras e espaços)
    if not name:
        raise HTTPException(status_code=400, detail="Nome não pode ser vazio")
    
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Nome muito curto")
    
    if len(name) > 50:
        raise HTTPException(status_code=400, detail="Nome muito longo")
    
    # Verificar se contém apenas letras, espaços e acentos
    import re
    if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', name):
        raise HTTPException(status_code=400, detail="Nome deve conter apenas letras")
    
    # Verificar se não é uma frase (máximo 3 palavras)
    words = name.split()
    if len(words) > 3:
        raise HTTPException(status_code=400, detail="Digite apenas seu nome (máximo 3 palavras)")
    
    await db.users.update_one(
        {"id": current_user["user_id"]},
        {"$set": {
            "display_name": name,
            "name_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True, "name": name}

@api_router.post("/users/me/avatar")
async def upload_user_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload de foto de perfil do cliente"""
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Validar tipo de arquivo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")
    
    # Generate unique filename
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"avatar_{current_user['user_id']}{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/uploads/{filename}"
    
    # Atualizar custom_avatar do usuário
    await db.users.update_one(
        {"id": current_user["user_id"]},
        {"$set": {"custom_avatar": url}}
    )
    
    return {"ok": True, "avatar_url": url}

# Agent routes (admin/reseller)
@api_router.get("/agents")
async def list_agents(request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    
    # Filtro baseado no tenant
    query = {}
    
    # Admin master vê todos, reseller vê apenas seus agentes
    if current_user["user_type"] == "admin" and not tenant.is_master:
        # Admin master acessando domínio de revenda específica
        if tenant.reseller_id:
            query["reseller_id"] = tenant.reseller_id
    elif current_user["user_type"] == "reseller":
        # Reseller vê apenas seus agentes
        query["reseller_id"] = current_user.get("reseller_id")
    elif current_user["user_type"] == "client":
        # Client vê lista geral (sem filtro sensível)
        if tenant.reseller_id:
            query["reseller_id"] = tenant.reseller_id
    
    agents = await db.agents.find(query, {"_id": 0, "pass_hash": 0}).to_list(None)
    return agents


@api_router.get("/agents/me")
async def get_current_agent(current_user: dict = Depends(get_current_user)):
    """Retorna informações do agente logado"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Apenas agentes podem acessar")
    
    agent = await db.agents.find_one({"id": current_user["user_id"]})
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return {
        "id": agent["id"],
        "name": agent["name"],
        "login": agent["login"],
        "department_ids": agent.get("department_ids", []),
        "avatar": agent.get("avatar", ""),
        "custom_avatar": agent.get("custom_avatar", "")
    }

@api_router.get("/agents/online-status")
async def get_online_status():
    # Check how many agents are connected via WebSocket
    online_count = len([uid for uid in manager.active_connections.keys() 
                       if uid.startswith('agent') or await db.agents.find_one({"id": uid})])
    return {"online": online_count, "status": "online" if online_count > 0 else "offline"}

@api_router.post("/agents")
async def create_agent(data: AgentCreate, request: Request, current_user: dict = Depends(get_current_user)):
    # Admin ou Reseller podem criar agentes
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Determinar reseller_id
    tenant = get_request_tenant(request)
    reseller_id = None
    
    if current_user["user_type"] == "reseller":
        reseller_id = current_user.get("reseller_id")
    elif current_user["user_type"] == "admin":
        # Admin pode estar criando para uma revenda específica
        reseller_id = tenant.reseller_id
    
    # Verificar se login já existe no mesmo tenant
    query = {"login": data.login}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    existing = await db.agents.find_one(query)
    if existing:
        raise HTTPException(status_code=400, detail="Login já existe nesta revenda")
    
    agent_id = str(uuid.uuid4())
    pass_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    agent = {
        "id": agent_id,
        "name": data.name,
        "login": data.login,
        "pass_hash": pass_hash,
        "avatar": data.avatar,
        "custom_avatar": "",
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.agents.insert_one(agent)
    return {"ok": True, "id": agent_id}

@api_router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Verificar permissão de tenant
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Reseller só pode editar seus próprios agentes
    if current_user["user_type"] == "reseller":
        if agent.get("reseller_id") != current_user.get("reseller_id"):
            raise HTTPException(status_code=403, detail="Não autorizado")
    
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "login" in data:
        update_data["login"] = data["login"]
    if "password" in data and data["password"]:
        update_data["pass_hash"] = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    if "avatar" in data:
        update_data["avatar"] = data["avatar"]
    
    await db.agents.update_one({"id": agent_id}, {"$set": update_data})
    return {"ok": True}

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Verificar permissão de tenant
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Reseller só pode deletar seus próprios agentes
    if current_user["user_type"] == "reseller":
        if agent.get("reseller_id") != current_user.get("reseller_id"):
            raise HTTPException(status_code=403, detail="Não autorizado")
    
    await db.agents.delete_one({"id": agent_id})
    return {"ok": True}

@api_router.post("/users/{user_id}/confirm-whatsapp")
async def confirm_user_whatsapp(user_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Salva WhatsApp confirmado pelo cliente"""
    whatsapp_confirmed = data.get("whatsapp", "")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "whatsapp_confirmed": whatsapp_confirmed,
            "whatsapp_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True}

@api_router.get("/users/{user_id}/should-ask-whatsapp")
async def should_ask_whatsapp(user_id: str):
    """Verifica se deve mostrar pop-up de WhatsApp"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {"should_ask": False}
    
    # Verificar se já perguntou na última semana
    asked_at = user.get("whatsapp_asked_at")
    if asked_at:
        asked_date = datetime.fromisoformat(asked_at)
        days_since_asked = (datetime.now(timezone.utc) - asked_date).days
        if days_since_asked < 7:
            return {"should_ask": False, "days_until_next": 7 - days_since_asked}
    
    # Se nunca perguntou ou passou 1 semana, perguntar
    return {"should_ask": True}

# Ticket routes
@api_router.get("/tickets")
async def list_tickets(status: Optional[str] = None, request: Request = None, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    
    query = {}
    if status:
        query["status"] = status
    
    # Aplicar filtro de tenant
    if tenant.reseller_id:
        query["reseller_id"] = tenant.reseller_id
    elif current_user["user_type"] == "reseller":
        query["reseller_id"] = current_user.get("reseller_id")
    
    tickets = await db.tickets.find(query, {"_id": 0}).to_list(None)
    
    # Enrich with user data and last message info
    for ticket in tickets:
        user = await db.users.find_one({"id": ticket["client_id"]})
        if user:
            ticket["client_whatsapp"] = user["whatsapp"]
            ticket["client_name"] = user.get("display_name", "")
            ticket["client_avatar"] = user.get("custom_avatar") or user.get("avatar", "")
        
        # Get last message
        last_msg = await db.messages.find_one(
            {"ticket_id": ticket["id"]},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        ticket["last_message"] = last_msg
    
    # Sort: client messages first, then by recent
    tickets.sort(key=lambda t: (
        0 if t.get("last_message", {}).get("from_type") == "client" else 1,
        -(datetime.fromisoformat(t.get("last_message", {}).get("created_at", "2000-01-01T00:00:00+00:00")).timestamp() if t.get("last_message") else 0)
    ))
    
    return tickets

@api_router.post("/tickets/{ticket_id}/mark-read")
async def mark_ticket_as_read(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Marca ticket como lido (zera contador de não lidas)"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Apenas agentes podem marcar como lido")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"unread_count": 0}}
    )
    return {"ok": True}

@api_router.post("/tickets/{ticket_id}/select-department")
async def select_department(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Cliente seleciona um departamento"""
    department_id = data.get("department_id")
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id é obrigatório")
    
    # Verificar se o departamento existe
    department = await db.departments.find_one({"id": department_id})
    if not department:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    # Atualizar ticket
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "department_id": department_id,
            "awaiting_department_choice": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Criar mensagem de confirmação
    message = {
        "id": str(uuid.uuid4()),
        "ticket_id": ticket_id,
        "from_type": "system",
        "kind": "text",
        "text": f"✅ Você selecionou: {department['name']}. Um atendente irá te responder em breve.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reseller_id": current_user.get("reseller_id")
    }
    
    await db.messages.insert_one(message)
    
    # Enviar via WebSocket
    ticket = await db.tickets.find_one({"id": ticket_id})
    if ticket:
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": message
        })
    
    # TODO: Se departamento tem IA, acionar IA aqui
    
    return {"ok": True}


@api_router.get("/tickets/counts")
async def get_ticket_counts(request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    
    # Filtro baseado no tenant
    base_query = {}
    if tenant.reseller_id:
        base_query["reseller_id"] = tenant.reseller_id
    elif current_user["user_type"] == "reseller":
        base_query["reseller_id"] = current_user.get("reseller_id")
    
    em_espera = await db.tickets.count_documents({**base_query, "status": "EM_ESPERA"})
    atendendo = await db.tickets.count_documents({**base_query, "status": "ATENDENDO"})
    finalizadas = await db.tickets.count_documents({**base_query, "status": "FINALIZADAS"})
    return {
        "EM_ESPERA": em_espera,
        "ATENDENDO": atendendo,
        "FINALIZADAS": finalizadas
    }

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket

@api_router.post("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    status = data.get("status")
    if status not in ["EM_ESPERA", "ATENDENDO", "FINALIZADAS"]:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Notify client
    ticket = await db.tickets.find_one({"id": ticket_id})
    if ticket:
        await manager.send_to_user(ticket["client_id"], {
            "type": "ticket_status",
            "ticket_id": ticket_id,
            "status": status
        })
    
    return {"ok": True}

@api_router.post("/tickets/{ticket_id}/toggle-ai")
async def toggle_ai_in_ticket(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Ativa/desativa IA em uma conversa específica por 1 hora"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    # Toggle: se está desativado, reativa. Se está ativo, desativa por 1h
    current_disabled_until = ticket.get("ai_disabled_until")
    
    if current_disabled_until:
        # Se já está desativado, verificar se expirou
        try:
            disabled_until = datetime.fromisoformat(current_disabled_until)
            if datetime.now(timezone.utc) < disabled_until:
                # Ainda desativado, então reativar
                await db.tickets.update_one(
                    {"id": ticket_id},
                    {"$unset": {"ai_disabled_until": ""}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                return {"message": "IA reativada", "ai_enabled": True}
        except:
            pass
    
    # Desativar por 1 hora
    disabled_until = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "ai_disabled_until": disabled_until.isoformat(),
            "ai_disabled_by": current_user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "IA desativada por 1 hora", "ai_enabled": False, "disabled_until": disabled_until.isoformat()}

@api_router.put("/tickets/{ticket_id}/assign")
async def assign_ticket_to_agent(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Atribui ticket a um atendente"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    agent_id = data.get("agent_id", current_user["user_id"])  # Usa ID do usuário atual se não especificado
    
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "assigned_agent_id": agent_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Ticket atribuído", "assigned_agent_id": agent_id}

# Message routes
@api_router.get("/messages/{ticket_id}")
async def get_messages(ticket_id: str, limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find(
        {"ticket_id": ticket_id},
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(None)
    messages.reverse()
    return messages

@api_router.post("/messages")
async def send_message(data: MessageCreate, request: Request, current_user: dict = Depends(get_current_user)):
    # Validate sender - APENAS para clientes (admin e atendentes podem enviar por qualquer ID)
    user_type = current_user.get("user_type", "")
    
    if user_type == "client":
        # Clientes só podem enviar como eles mesmos
        if str(data.from_id) != str(current_user["user_id"]):
            logger.error(f"Client authorization failed: from_id={data.from_id}, user_id={current_user['user_id']}")
            raise HTTPException(status_code=403, detail=f"Não autorizado - ID não corresponde")
    else:
        # Admin e atendentes podem enviar mensagens em nome de qualquer ticket
        logger.info(f"Message from {user_type}: {data.from_id} (logged as {current_user['user_id']})")
    
    # Pegar tenant do request ou do token
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Get config for validation
    if reseller_id:
        config = await db.reseller_configs.find_one({"reseller_id": reseller_id}) or {}
    else:
        config = await db.config.find_one({"id": "config"}) or {}
    
    # Agent text validation - NEW ENHANCED VALIDATION
    if data.from_type == "agent" and data.kind == "text":
        # Nova validação com dados sensíveis
        error = await validate_sensitive_data(data.text, config)
        if error:
            raise HTTPException(status_code=400, detail=error)
    
    # Create or get ticket
    if data.from_type == "client":
        # Buscar ticket do cliente com filtro de tenant
        query = {"client_id": data.from_id}
        if reseller_id:
            query["reseller_id"] = reseller_id
        
        ticket = await db.tickets.find_one(query)
        if not ticket:
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "client_id": data.from_id,
                "status": "EM_ESPERA",
                "department_id": None,
                "awaiting_department_choice": True,
                "department_choice_sent_at": None,
                "unread_count": 0,
                "reseller_id": reseller_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
            
            # Enviar mensagem de seleção de departamento (primeira vez)
            await send_department_selection(ticket_id, data.from_id, reseller_id)
        else:
            ticket_id = ticket["id"]
            # Update ticket status to EM_ESPERA when client sends and increment unread
            await db.tickets.update_one(
                {"id": ticket_id},
                {
                    "$set": {"status": "EM_ESPERA", "updated_at": datetime.now(timezone.utc).isoformat()},
                    "$inc": {"unread_count": 1}  # Incrementar contador de não lidas
                }
            )
    else:
        ticket_id = data.ticket_id
        if not ticket_id:
            raise HTTPException(status_code=400, detail="ticket_id é obrigatório para mensagens de agente")
        # When agent sends, reset unread count
        if data.from_type == "agent":
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {"unread_count": 0}}
            )
    
    # Wrap text at 20 chars for client
    text = data.text
    if data.from_type == "client" and data.kind == "text":
        text = re.sub(r'(.{20})', r'\1\n', text)
    
    # Detectar se atendente está enviando chave PIX
    message_kind = data.kind
    pix_key = None
    if data.from_type == "agent" and data.kind == "text":
        # Buscar chave PIX configurada
        config_query = {"reseller_id": reseller_id} if reseller_id else {"id": "config"}
        config = await db.reseller_configs.find_one(config_query) or await db.config.find_one({"id": "config"}) or {}
        configured_pix = config.get("pix_key", "")
        
        # Se o texto contém a chave PIX configurada, transformar em mensagem PIX
        if configured_pix and configured_pix in text:
            message_kind = "pix"
            pix_key = configured_pix
            text = f"💰 Clique no botão abaixo para copiar a chave PIX"
    
    # Create message
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "ticket_id": ticket_id,
        "from_type": data.from_type,
        "from_id": data.from_id,
        "to_type": data.to_type,
        "to_id": data.to_id,
        "kind": message_kind,
        "text": text,
        "pix_key": pix_key,  # Adicionar chave PIX se for mensagem tipo pix
        "file_url": data.file_url or "",
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(message)
    
    # Check auto-reply (exact match only)
    if data.from_type == "client" and data.kind == "text":
        # Buscar config do reseller ou config principal
        if reseller_id:
            config = await db.reseller_configs.find_one({"reseller_id": reseller_id})
        else:
            config = await db.config.find_one({"id": "config"})
        
        if config:
            auto_replies = config.get("auto_reply", [])
            text_lower = text.lower().strip()
            for rule in auto_replies:
                q = rule.get("q", "").lower().strip()
                # EXACT match only
                if q and text_lower == q:
                    # Buscar agente do mesmo tenant
                    agent_query = {}
                    if reseller_id:
                        agent_query["reseller_id"] = reseller_id
                    agents = await db.agents.find(agent_query).to_list(1)
                    if agents:
                        agent = agents[0]
                        reply_id = str(uuid.uuid4())
                        reply = {
                            "id": reply_id,
                            "ticket_id": ticket_id,
                            "from_type": "agent",
                            "from_id": agent["id"],
                            "to_type": "client",
                            "to_id": data.from_id,
                            "kind": "text",
                            "text": rule.get("a", ""),
                            "file_url": "",
                            "reseller_id": reseller_id,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.messages.insert_one(reply)
                        await db.tickets.update_one(
                            {"id": ticket_id},
                            {"$set": {"status": "ATENDENDO"}}
                        )
                        # Notify client of auto-reply
                        await manager.send_to_user(data.from_id, {
                            "type": "message",
                            "message": reply
                        })
                    break
    
    # Processar com IA se houver agente IA vinculado ao departamento
    ai_logger.info(f"🟡 Verificando se deve chamar IA: from_type={data.from_type}, kind={data.kind}")
    if data.from_type == "client" and data.kind == "text":
        ai_logger.info(f"🟡 Mensagem de cliente detectada! ticket_id={ticket_id}")
        # Buscar ticket atualizado
        ticket = await db.tickets.find_one({"id": ticket_id})
        ai_logger.info(f"🟡 Ticket encontrado: {ticket.get('id') if ticket else 'None'}, department_id={ticket.get('department_id') if ticket else 'None'}")
        if ticket and ticket.get("department_id"):
            ai_logger.info(f"🟡 Chamando process_message_with_ai para ticket {ticket['id']}")
            # Chamar IA de forma assíncrona (não bloqueia resposta)
            asyncio.create_task(process_message_with_ai(ticket, text, reseller_id))
        elif ticket and not ticket.get("department_id"):
            ai_logger.info(f"⚠️ Ticket {ticket['id']} existe mas NÃO TEM department_id definido. IA não será chamada.")
        elif not ticket:
            ai_logger.error(f"💥 Ticket {ticket_id} não encontrado no banco!")
    else:
        ai_logger.info(f"⚪ Mensagem não é de cliente ou não é texto: from_type={data.from_type}, kind={data.kind}")
    
    # Send via WebSocket to recipient
    await manager.send_to_user(data.to_id, {
        "type": "message",
        "message": message
    })
    
    # Send to sender as well (for real-time update in their own chat)
    await manager.send_to_user(data.from_id, {
        "type": "message",
        "message": message
    })
    
    # If client sent, notify all agents
    if data.from_type == "client":
        await manager.broadcast_to_agents({
            "type": "message",
            "message": message
        })
    
    # If agent sent, make sure client receives it
    if data.from_type == "agent":
        await manager.send_to_user(data.to_id, {
            "type": "message",
            "message": message
        })
    
    return {"ok": True, "message_id": message_id}

# Upload route
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Generate unique filename
    ext = Path(file.filename).suffix or ".bin"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Determine file kind
    mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    kind = "file"
    if mime_type.startswith("image/"):
        kind = "image"
    elif mime_type.startswith("video/"):
        kind = "video"
    elif mime_type.startswith("audio/"):
        kind = "audio"
    
    url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/uploads/{filename}"
    return {"ok": True, "url": url, "kind": kind}

# Config routes (admin only)
@api_router.get("/config")
async def get_config(request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Se for reseller ou tenant específico, buscar config da revenda
    if reseller_id:
        config = await db.reseller_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
        if not config:
            config = {
                "id": f"config_{reseller_id}",
                "reseller_id": reseller_id,
                "quick_blocks": [],
                "auto_reply": [],
                "apps": [],
                "pix_key": "",
                "support_avatar": f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/icon-512.png",
                "allowed_data": {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
                "api_integration": {"api_url": "", "api_token": "", "api_enabled": False},
                "ai_agent": {
                    "name": "Assistente IA",
                    "personality": "",
                    "instructions": "",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "api_key": "",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "mode": "standby",
                    "active_hours": "24/7",
                    "enabled": False,
                    "can_access_credentials": True,
                    "knowledge_base": ""
                }
            }
            await db.reseller_configs.insert_one(config)
    else:
        # Config principal (admin master)
        config = await db.config.find_one({"id": "config"}, {"_id": 0})
        if not config:
            config = {
                "id": "config",
                "quick_blocks": [],
                "auto_reply": [],
                "apps": [],
                "pix_key": "",
                "support_avatar": f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/icon-512.png",
                "allowed_data": {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
                "api_integration": {"api_url": "", "api_token": "", "api_enabled": False},
                "ai_agent": {
                    "name": "Assistente IA",
                    "personality": "",
                    "instructions": "",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "api_key": "",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "mode": "standby",
                    "active_hours": "24/7",
                    "enabled": False,
                    "can_access_credentials": True,
                    "knowledge_base": ""
                }
            }
            await db.config.insert_one(config)
    
    # Garantir que todos os campos existam (para configs antigas)
    if "pix_key" not in config:
        config["pix_key"] = ""
    if "allowed_data" not in config:
        config["allowed_data"] = {"cpfs": [], "emails": [], "phones": [], "random_keys": []}
    if "api_integration" not in config:
        config["api_integration"] = {"api_url": "", "api_token": "", "api_enabled": False}
    if "ai_agent" not in config:
        config["ai_agent"] = {
            "name": "Assistente IA",
            "personality": "",
            "instructions": "",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500,
            "mode": "standby",
            "active_hours": "24/7",
            "enabled": False,
            "can_access_credentials": True,
            "knowledge_base": ""
        }
    
    return config

@api_router.put("/config")
async def update_config(data: ConfigData, request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Admin ou Reseller podem atualizar config
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Preparar dados para salvar
    config_data = {
        "quick_blocks": [b.dict() for b in data.quick_blocks],
        "auto_reply": [a.dict() for a in data.auto_reply],
        "apps": [app.dict() for app in data.apps],
        "pix_key": data.pix_key or "",
        "allowed_data": data.allowed_data.dict() if data.allowed_data else {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
        "api_integration": data.api_integration.dict() if data.api_integration else {"api_url": "", "api_token": "", "api_enabled": False},
        "ai_agent": data.ai_agent.dict() if data.ai_agent else {
            "name": "Assistente IA",
            "personality": "",
            "instructions": "",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500,
            "mode": "standby",
            "active_hours": "24/7",
            "enabled": False,
            "can_access_credentials": True,
            "knowledge_base": ""
        }
    }
    
    # Se for reseller, atualizar config da revenda
    if reseller_id:
        await db.reseller_configs.update_one(
            {"reseller_id": reseller_id},
            {"$set": config_data},
            upsert=True
        )
    else:
        # Config principal (admin master)
        if current_user["user_type"] != "admin":
            raise HTTPException(status_code=403, detail="Não autorizado")
        
        await db.config.update_one(
            {"id": "config"},
            {"$set": config_data},
            upsert=True
        )
    return {"ok": True}

@api_router.post("/config/support-avatar")
async def upload_support_avatar(file: UploadFile = File(...), request: Request = None, current_user: dict = Depends(get_current_user)):
    """Upload de logo/foto do suporte (Admin/Reseller)"""
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Admin ou Reseller podem fazer upload
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Validar tipo de arquivo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")
    
    # Generate unique filename
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"support_avatar_{reseller_id or 'admin'}{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Adicionar timestamp para forçar atualização do cache
    timestamp = int(datetime.now(timezone.utc).timestamp())
    url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/uploads/{filename}?t={timestamp}"
    
    # Atualizar support_avatar na configuração
    if reseller_id:
        await db.reseller_configs.update_one(
            {"reseller_id": reseller_id},
            {"$set": {"support_avatar": url}},
            upsert=True
        )
    else:
        await db.configs.update_one(
            {"id": "config"},
            {"$set": {"support_avatar": url}},
            upsert=True
        )
    
    return {"ok": True, "avatar_url": url}

# Notice routes
@api_router.get("/notices")
async def get_notices(request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Get notices from last 60 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=60)
    
    query = {"created_at": {"$gte": cutoff.isoformat()}}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    notices = await db.notices.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    return notices

@api_router.post("/notices")
async def create_notice(data: NoticeCreate, request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    notice_id = str(uuid.uuid4())
    notice = {
        "id": notice_id,
        "kind": data.kind,
        "text": data.text or "",
        "file_url": data.file_url or "",
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notices.insert_one(notice)
    return {"ok": True, "notice_id": notice_id}

# Pin credentials (agent only)
@api_router.get("/users/{user_id}/credentials")
async def get_user_credentials(user_id: str, current_user: dict = Depends(get_current_user)):
    """Buscar credenciais fixadas de um cliente específico (apenas para agentes)"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }

@api_router.put("/users/{user_id}/pin-credentials")
async def set_pin_credentials(user_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "pinned_user": data.get("pinned_user", ""),
            "pinned_pass": data.get("pinned_pass", "")
        }}
    )
    
    # Notify client
    await manager.send_to_user(user_id, {
        "type": "credentials_updated",
        "pinned_user": data.get("pinned_user", ""),
        "pinned_pass": data.get("pinned_pass", "")
    })
    
    return {"ok": True}

# Reset PIN (agent only)
@api_router.post("/users/reset-pin")
async def reset_pin(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    whatsapp = data.get("whatsapp", "")
    user = await db.users.find_one({"whatsapp": whatsapp})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await db.users.update_one({"id": user["id"]}, {"$set": {"pin_hash": ""}})
    return {"ok": True}

# WebSocket endpoint
@api_router.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await manager.connect(websocket, user_id, session_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Auto-Responder endpoints (legado - mantido para compatibilidade)
@api_router.get("/config/auto-responses")
async def get_auto_responses(current_user: dict = Depends(get_current_user)):
    config = await db.config.find_one({"id": "auto_responses"}) or {}
    return config.get("responses", [])

@api_router.post("/config/auto-responses")
async def save_auto_responses(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    await db.config.update_one(
        {"id": "auto_responses"},
        {"$set": {"responses": data.get("responses", [])}},
        upsert=True
    )
    return {"ok": True}

# ====== NOVO: Auto-Responder Avançado (Multi-mídia + Delays) ======
@api_router.get("/config/auto-responder-sequences")
async def get_auto_responder_sequences(current_user: dict = Depends(get_current_user)):
    """Retorna todas as sequências de auto-responder"""
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    sequences = await db.auto_responder_sequences.find(
        {"reseller_id": reseller_id},
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).to_list(length=None)
    
    return sequences

@api_router.post("/config/auto-responder-sequences")
async def save_auto_responder_sequences(data: dict, current_user: dict = Depends(get_current_user)):
    """Salva/atualiza uma sequência de auto-responder"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    sequences = data.get("sequences", [])
    
    # Remove todas as sequências existentes desta revenda
    await db.auto_responder_sequences.delete_many({"reseller_id": reseller_id})
    
    # Insere novas sequências
    if sequences:
        for seq in sequences:
            seq["reseller_id"] = reseller_id
        await db.auto_responder_sequences.insert_many(sequences)
    
    return {"ok": True, "count": len(sequences)}

@api_router.delete("/config/auto-responder-sequences/{sequence_id}")
async def delete_auto_responder_sequence(sequence_id: str, current_user: dict = Depends(get_current_user)):
    """Deleta uma sequência específica"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    result = await db.auto_responder_sequences.delete_one({
        "id": sequence_id,
        "reseller_id": reseller_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sequência não encontrada")
    
    return {"ok": True}

# ====== NOVO: Tutorials Avançado (Multi-mídia + Delays) ======
@api_router.get("/config/tutorials-advanced")
async def get_tutorials_advanced(current_user: dict = Depends(get_current_user)):
    """Retorna todos os tutoriais avançados"""
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    tutorials = await db.tutorials_advanced.find(
        {"reseller_id": reseller_id},
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).to_list(length=None)
    
    return tutorials

@api_router.post("/config/tutorials-advanced")
async def save_tutorials_advanced(data: dict, current_user: dict = Depends(get_current_user)):
    """Salva/atualiza tutoriais avançados"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    tutorials = data.get("tutorials", [])
    
    # Remove todos os tutoriais existentes desta revenda
    await db.tutorials_advanced.delete_many({"reseller_id": reseller_id})
    
    # Insere novos tutoriais
    if tutorials:
        for tutorial in tutorials:
            tutorial["reseller_id"] = reseller_id
        await db.tutorials_advanced.insert_many(tutorials)
    
    return {"ok": True, "count": len(tutorials)}

@api_router.delete("/config/tutorials-advanced/{tutorial_id}")
async def delete_tutorial_advanced(tutorial_id: str, current_user: dict = Depends(get_current_user)):
    """Deleta um tutorial específico"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    reseller_id = tenant_ctx.reseller_id
    
    result = await db.tutorials_advanced.delete_one({
        "id": tutorial_id,
        "reseller_id": reseller_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tutorial não encontrado")
    
    return {"ok": True}

# ====== NOVO: Gestão de Domínios para Revendas ======
@api_router.get("/reseller/domain-info")
async def get_reseller_domain_info(request: Request, current_user: dict = Depends(get_current_user)):
    """Retorna informações de domínio da revenda"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem acessar")
    
    # Buscar informações da revenda
    reseller = await db.resellers.find_one({"id": reseller_id})
    if not reseller:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    # IP do servidor (você deve configurar este valor)
    # Em produção, isso viria de uma configuração
    server_ip = os.environ.get('SERVER_IP', '198.51.100.1')  # IP de exemplo
    
    # Domínio de teste (gerado automaticamente)
    test_domain = reseller.get('domain', f"{reseller_id}.preview.emergentagent.com")
    
    return {
        "test_domain": test_domain,
        "custom_domain": reseller.get('custom_domain', ''),
        "custom_domain_verified": reseller.get('custom_domain_verified', False),
        "server_ip": server_ip,
        "ssl_enabled": True
    }

@api_router.post("/reseller/update-domain")
async def update_reseller_domain(data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Atualiza o domínio personalizado da revenda"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem atualizar")
    
    custom_domain = data.get('custom_domain', '').strip().lower()
    
    if not custom_domain:
        raise HTTPException(status_code=400, detail="Domínio inválido")
    
    # Atualizar revenda
    await db.resellers.update_one(
        {"id": reseller_id},
        {"$set": {
            "custom_domain": custom_domain,
            "custom_domain_verified": False,  # Precisa verificar DNS
            "custom_domain_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"ok": True, "message": "Domínio salvo. Configure o DNS e aguarde verificação."}

@api_router.get("/reseller/verify-domain")
async def verify_reseller_domain(request: Request, current_user: dict = Depends(get_current_user)):
    """Verifica se o DNS do domínio personalizado está configurado corretamente"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem verificar")
    
    reseller = await db.resellers.find_one({"id": reseller_id})
    if not reseller or not reseller.get('custom_domain'):
        raise HTTPException(status_code=400, detail="Nenhum domínio personalizado configurado")
    
    custom_domain = reseller['custom_domain']
    
    # Aqui você implementaria a verificação DNS real
    # Por ora, vamos simular
    try:
        import socket
        # Tentar resolver o domínio
        ip = socket.gethostbyname(custom_domain)
        server_ip = os.environ.get('SERVER_IP', '198.51.100.1')
        
        if ip == server_ip:
            # DNS configurado corretamente
            await db.resellers.update_one(
                {"id": reseller_id},
                {"$set": {
                    "custom_domain_verified": True,
                    "custom_domain_verified_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"verified": True, "message": "Domínio verificado com sucesso!"}
        else:
            return {"verified": False, "message": f"DNS aponta para {ip}, esperado {server_ip}"}
    
    except socket.gaierror:
        return {"verified": False, "message": "Domínio não encontrado. Aguarde propagação DNS."}
    except Exception as e:
        return {"verified": False, "message": f"Erro ao verificar: {str(e)}"}

# Tutoriais endpoints (legado - mantido para compatibilidade)
@api_router.get("/config/tutorials")
async def get_tutorials(current_user: dict = Depends(get_current_user)):
    config = await db.config.find_one({"id": "tutorials"}) or {}
    return config.get("tutorials", [])

@api_router.post("/config/tutorials")
async def save_tutorials(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    await db.config.update_one(
        {"id": "tutorials"},
        {"$set": {"tutorials": data.get("tutorials", [])}},
        upsert=True
    )
    return {"ok": True}

app.include_router(api_router)

# Include reseller routes
try:
    from reseller_routes import reseller_router
    app.include_router(reseller_router)
    print("✅ Reseller routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load reseller routes: {e}")
    import traceback
    traceback.print_exc()

# Include AI agent routes
try:
    from ai_agent_routes import ai_router
    app.include_router(ai_router)
    print("✅ AI agent routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load AI agent routes: {e}")
    import traceback
    traceback.print_exc()

# Serve uploads
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Tenant Detection Middleware
class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Detectar tenant pelo domínio
        tenant_ctx = await detect_tenant(request, db)
        
        # Armazenar no contexto global
        global_tenant_context.reseller_id = tenant_ctx.reseller_id
        global_tenant_context.reseller_data = tenant_ctx.reseller_data
        global_tenant_context.is_master = tenant_ctx.is_master
        
        # Adicionar ao request state para acesso nas rotas
        request.state.tenant = tenant_ctx
        
        response = await call_next(request)
        return response

app.add_middleware(TenantMiddleware)

@app.get("/api/debug/tenant")
async def debug_tenant(request: Request):
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    
    return {
        "domain": request.headers.get("host", ""),
        "tenant_id": tenant_ctx.reseller_id,
        "is_master": tenant_ctx.is_master,
        "tenant_data": tenant_ctx.reseller_data.get("name") if tenant_ctx.reseller_data else None
    }

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
