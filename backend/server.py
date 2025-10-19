from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Set
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import aiofiles
from models import *
import mimetypes
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'support_chat')]

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'sua-chave-secreta-super-segura-aqui')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Allowed PIX keys
PIX_ALLOWED = [
    "7c11dc15-ea60-493e-9e7d-adfd317c58a4",
    "5b80155d-28cb-4c2c-88df-e2240fa8e5c5"
]

# Uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI()
api_router = APIRouter(prefix="/api")

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
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    async def broadcast_to_agents(self, message: dict):
        agents = await db.agents.find({}, {"id": 1}).to_list(None)
        for agent in agents:
            await self.send_to_user(agent["id"], message)

manager = ConnectionManager()

# Auth helpers
def create_token(user_id: str, user_type: str) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": datetime.now(timezone.utc) + timedelta(days=365)  # Token válido por 1 ano
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

# Validation helpers
def is_forbidden_text(text: str) -> Optional[str]:
    text_lower = text.lower()
    
    # Email check
    if re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, re.IGNORECASE):
        return "E-mail não permitido."
    
    # Phone check
    if re.search(r'\b(\+?55)?\D*\(?\d{2}\)?\D*\d{4,5}\D*\d{4}\b', text):
        return "Telefone não permitido."
    
    # CPF check
    if re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text) or re.search(r'\b\d{11}\b', text):
        return "CPF não permitido."
    
    # PIX UUID check
    uuids = re.findall(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', text, re.IGNORECASE)
    for uuid_str in uuids:
        if uuid_str.lower() not in [p.lower() for p in PIX_ALLOWED]:
            return "Chave Pix não autorizada."
    
    return None

# Auth routes
@api_router.post("/auth/admin/login")
async def admin_login(data: AdminLogin):
    if data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    token = create_token("admin", "admin")
    return TokenResponse(token=token, user_type="admin", user_data={"id": "admin"})

@api_router.post("/auth/agent/login")
async def agent_login(data: AgentLogin):
    agent = await db.agents.find_one({"login": data.login})
    if not agent or not bcrypt.checkpw(data.password.encode(), agent["pass_hash"].encode()):
        raise HTTPException(status_code=401, detail="Login ou senha inválidos")
    token = create_token(agent["id"], "agent")
    return TokenResponse(token=token, user_type="agent", user_data={
        "id": agent["id"],
        "name": agent["name"],
        "avatar": agent.get("custom_avatar") or agent.get("avatar", "")
    })

@api_router.post("/auth/client/login")
async def client_login(data: UserLogin):
    user = await db.users.find_one({"whatsapp": data.whatsapp})
    
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
    
    token = create_token(user["id"], "client")
    return TokenResponse(token=token, user_type="client", user_data={
        "id": user["id"],
        "whatsapp": user["whatsapp"],
        "display_name": user.get("display_name", ""),
        "avatar": user.get("custom_avatar") or user.get("avatar", ""),
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    })

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
async def update_pin(data: dict, current_user: dict = Depends(get_current_user)):
    pin = data.get("pin", "")
    if len(pin) != 2 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve ter 2 dígitos")
    
    pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": {"pin_hash": pin_hash}})
    return {"ok": True}

# Agent routes (admin only)
@api_router.get("/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    # Allow clients to see agents list (but without sensitive data)
    agents = await db.agents.find({}, {"_id": 0, "pass_hash": 0}).to_list(None)
    return agents

@api_router.get("/agents/online-status")
async def get_online_status():
    # Check how many agents are connected via WebSocket
    online_count = len([uid for uid in manager.active_connections.keys() 
                       if uid.startswith('agent') or await db.agents.find_one({"id": uid})])
    return {"online": online_count, "status": "online" if online_count > 0 else "offline"}

@api_router.post("/agents")
async def create_agent(data: AgentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    existing = await db.agents.find_one({"login": data.login})
    if existing:
        raise HTTPException(status_code=400, detail="Login já existe")
    
    agent_id = str(uuid.uuid4())
    pass_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    agent = {
        "id": agent_id,
        "name": data.name,
        "login": data.login,
        "pass_hash": pass_hash,
        "avatar": data.avatar,
        "custom_avatar": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.agents.insert_one(agent)
    return {"ok": True, "id": agent_id}

@api_router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
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
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    await db.agents.delete_one({"id": agent_id})
    return {"ok": True}

# Ticket routes
@api_router.get("/tickets")
async def list_tickets(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    
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

@api_router.get("/tickets/counts")
async def get_ticket_counts(current_user: dict = Depends(get_current_user)):
    em_espera = await db.tickets.count_documents({"status": "EM_ESPERA"})
    atendendo = await db.tickets.count_documents({"status": "ATENDENDO"})
    finalizadas = await db.tickets.count_documents({"status": "FINALIZADAS"})
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
async def send_message(data: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Validate sender
    logger.info(f"Message from: {data.from_id}, User: {current_user['user_id']}, Type: {current_user['user_type']}")
    if str(data.from_id) != str(current_user["user_id"]):
        logger.error(f"Authorization failed: from_id={data.from_id}, user_id={current_user['user_id']}")
        raise HTTPException(status_code=403, detail=f"Não autorizado - ID não corresponde")
    
    # Agent text validation
    if data.from_type == "agent" and data.kind == "text":
        error = is_forbidden_text(data.text)
        if error:
            raise HTTPException(status_code=400, detail=error)
    
    # Create or get ticket
    if data.from_type == "client":
        ticket = await db.tickets.find_one({"client_id": data.from_id})
        if not ticket:
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "client_id": data.from_id,
                "status": "EM_ESPERA",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
        else:
            ticket_id = ticket["id"]
            # Update ticket status to EM_ESPERA when client sends
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {"status": "EM_ESPERA", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
    else:
        ticket_id = data.ticket_id
    
    # Wrap text at 20 chars for client
    text = data.text
    if data.from_type == "client" and data.kind == "text":
        text = re.sub(r'(.{20})', r'\1\n', text)
    
    # Create message
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "ticket_id": ticket_id,
        "from_type": data.from_type,
        "from_id": data.from_id,
        "to_type": data.to_type,
        "to_id": data.to_id,
        "kind": data.kind,
        "text": text,
        "file_url": data.file_url or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(message)
    
    # Check auto-reply (exact match only)
    if data.from_type == "client" and data.kind == "text":
        config = await db.config.find_one({"id": "config"})
        if config:
            auto_replies = config.get("auto_reply", [])
            text_lower = text.lower().strip()
            for rule in auto_replies:
                q = rule.get("q", "").lower().strip()
                # EXACT match only
                if q and text_lower == q:
                    # Send auto reply
                    agents = await db.agents.find({}).to_list(1)
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
    
    # Send via WebSocket
    await manager.send_to_user(data.to_id, {
        "type": "message",
        "message": message
    })
    
    # If client sent, notify all agents
    if data.from_type == "client":
        await manager.broadcast_to_agents({
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
async def get_config(current_user: dict = Depends(get_current_user)):
    config = await db.config.find_one({"id": "config"}, {"_id": 0})
    if not config:
        config = {
            "id": "config",
            "quick_blocks": [],
            "auto_reply": [],
            "apps": []
        }
        await db.config.insert_one(config)
    return config

@api_router.put("/config")
async def update_config(data: ConfigData, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    await db.config.update_one(
        {"id": "config"},
        {"$set": {
            "quick_blocks": [b.dict() for b in data.quick_blocks],
            "auto_reply": [a.dict() for a in data.auto_reply],
            "apps": [app.dict() for app in data.apps]
        }},
        upsert=True
    )
    return {"ok": True}

# Notice routes
@api_router.get("/notices")
async def get_notices():
    # Get notices from last 60 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=60)
    notices = await db.notices.find(
        {"created_at": {"$gte": cutoff.isoformat()}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    return notices

@api_router.post("/notices")
async def create_notice(data: NoticeCreate, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    notice_id = str(uuid.uuid4())
    notice = {
        "id": notice_id,
        "kind": data.kind,
        "text": data.text or "",
        "file_url": data.file_url or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notices.insert_one(notice)
    return {"ok": True, "notice_id": notice_id}

# Pin credentials (agent only)
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

# Serve uploads
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

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
