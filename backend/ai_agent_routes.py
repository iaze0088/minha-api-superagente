"""
Rotas para gerenciamento de Agentes IA e Departamentos
"""
import os
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import List
import uuid
from datetime import datetime, timezone
from models import *
from motor.motor_asyncio import AsyncIOMotorClient
from tenant_helpers import get_tenant_filter
import jwt

# Configuração do MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ.get("DB_NAME", "support_chat")]

# Configuração do JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key-change-in-production')

ai_router = APIRouter(prefix="/api/ai", tags=["ai-agents"])

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    token = authorization.replace('Bearer ', '')
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================
# ROTAS DE AGENTES IA
# ============================================

@ai_router.get("/agents", response_model=List[AIAgentFull])
async def list_ai_agents(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os agentes IA da revenda"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    agents = await db.ai_agents.find(query).to_list(length=None)
    return [AIAgentFull(**agent) for agent in agents]

@ai_router.post("/agents", response_model=AIAgentFull)
async def create_ai_agent(
    data: AIAgentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id baseado no contexto
    from tenant_middleware import get_request_tenant
    tenant = get_request_tenant(request)
    user_type = current_user.get("user_type")
    
    # Admin master: usa tenant do request (None se for master domain)
    if user_type == "admin" and tenant.is_master:
        reseller_id = tenant.reseller_id
    else:
        # Reseller: usa reseller_id do token
        reseller_id = current_user.get("reseller_id")
    
    agent = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description or "",
        "who_is": "",
        "what_does": "",
        "objective": "",
        "how_respond": "",
        "instructions": "",
        "avoid_topics": "",
        "avoid_words": "",
        "allowed_links": "",
        "custom_rules": "",
        "knowledge_base": "",
        "llm_provider": data.llm_provider,
        "llm_model": data.llm_model,
        "api_key": "",
        "temperature": 0.5,
        "max_tokens": 500,
        "auto_detect_language": True,
        "knowledge_restriction": False,
        "timezone": "America/Sao_Paulo",
        "is_active": True,
        "linked_agents": getattr(data, 'linked_agents', []),
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.ai_agents.insert_one(agent)
    return AIAgentFull(**agent)

@ai_router.get("/agents/{agent_id}", response_model=AIAgentFull)
async def get_ai_agent(
    agent_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Busca um agente IA por ID"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": agent_id}
    query.update(tenant_filter)
    
    agent = await db.ai_agents.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return AIAgentFull(**agent)

@ai_router.put("/agents/{agent_id}", response_model=AIAgentFull)
async def update_ai_agent(
    agent_id: str,
    data: AIAgentUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": agent_id}
    query.update(tenant_filter)
    
    agent = await db.ai_agents.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Atualizar apenas campos fornecidos
    update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.ai_agents.update_one(query, {"$set": update_data})
    
    updated_agent = await db.ai_agents.find_one(query)
    return AIAgentFull(**updated_agent)

@ai_router.delete("/agents/{agent_id}")
async def delete_ai_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    reseller_id = current_user.get("reseller_id")
    
    query = {"id": agent_id}
    if reseller_id:
        query["reseller_id"] = reseller_id
    elif current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    result = await db.ai_agents.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return {"ok": True}

# ============================================
# ROTAS DE DEPARTAMENTOS
# ============================================

@ai_router.get("/departments", response_model=List[Department])
async def list_departments(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os departamentos da revenda"""
    reseller_id = current_user.get("reseller_id")
    
    query = {}
    if reseller_id:
        query["reseller_id"] = reseller_id
    elif current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    departments = await db.departments.find(query).to_list(length=None)
    return [Department(**dept) for dept in departments]

@ai_router.post("/departments", response_model=Department)
async def create_department(
    data: DepartmentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    reseller_id = current_user.get("reseller_id")
    
    # Se marcar como default, desmarcar os outros
    if data.is_default:
        query = {"reseller_id": reseller_id} if reseller_id else {}
        await db.departments.update_many(query, {"$set": {"is_default": False}})
    
    department = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description or "",
        "ai_agent_id": data.ai_agent_id,
        "is_default": data.is_default,
        "timeout_seconds": data.timeout_seconds,
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.departments.insert_one(department)
    return Department(**department)

@ai_router.put("/departments/{dept_id}", response_model=Department)
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    reseller_id = current_user.get("reseller_id")
    
    query = {"id": dept_id}
    if reseller_id:
        query["reseller_id"] = reseller_id
    elif current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    department = await db.departments.find_one(query)
    if not department:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    # Se marcar como default, desmarcar os outros
    if data.is_default:
        query_update = {"reseller_id": reseller_id} if reseller_id else {}
        await db.departments.update_many(query_update, {"$set": {"is_default": False}})
    
    # Atualizar apenas campos fornecidos
    update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    
    await db.departments.update_one(query, {"$set": update_data})
    
    updated_dept = await db.departments.find_one(query)
    return Department(**updated_dept)

@ai_router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    reseller_id = current_user.get("reseller_id")
    
    query = {"id": dept_id}
    if reseller_id:
        query["reseller_id"] = reseller_id
    elif current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    result = await db.departments.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    return {"ok": True}
