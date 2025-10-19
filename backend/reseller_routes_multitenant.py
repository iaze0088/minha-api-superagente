"""
Rotas para gerenciamento de revendas com suporte a multi-tenant e hierarquia.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from models import *
import jwt
import logging

logger = logging.getLogger(__name__)

reseller_router = APIRouter(prefix="/api/resellers", tags=["resellers"])

JWT_SECRET = "sua-chave-secreta-super-segura-aqui-2024"

def create_token(user_id: str, user_type: str, reseller_id: Optional[str] = None) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "reseller_id": reseller_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=365)
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

# Get db dependency
def get_db_dep():
    from server import db
    return db

# Helper: calcular nível hierárquico
async def calculate_level(parent_id: Optional[str], db) -> int:
    """Calcula o nível baseado no parent_id"""
    if not parent_id:
        return 0  # Nível raiz
    
    parent = await db.resellers.find_one({"id": parent_id})
    if not parent:
        raise HTTPException(status_code=404, detail="Revenda pai não encontrada")
    
    return parent.get("level", 0) + 1

# Helper: contar filhos
async def count_children(reseller_id: str, db) -> int:
    """Conta quantas sub-revendas tem"""
    return await db.resellers.count_documents({"parent_id": reseller_id})

# Helper: verificar se pode deletar
async def can_delete_reseller(reseller_id: str, db) -> tuple[bool, str]:
    """Verifica se a revenda pode ser deletada"""
    children_count = await count_children(reseller_id, db)
    if children_count > 0:
        return False, f"Esta revenda possui {children_count} sub-revenda(s). Entre em contato com o Admin Master para transferência."
    return True, ""

# Reseller authentication
@reseller_router.post("/login")
async def reseller_login(data: ResellerLogin):
    db = get_db_dep()
    reseller = await db.resellers.find_one({"email": data.email})
    if not reseller or not bcrypt.checkpw(data.password.encode(), reseller["pass_hash"].encode()):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    if not reseller.get("is_active", True):
        raise HTTPException(status_code=403, detail="Revenda desativada")
    
    token = create_token(reseller["id"], "reseller", reseller["id"])
    
    return TokenResponse(
        token=token,
        user_type="reseller",
        user_data={
            "id": reseller["id"],
            "name": reseller["name"],
            "email": reseller["email"],
            "domain": reseller.get("domain", ""),
            "custom_domain": reseller.get("custom_domain", ""),
            "level": reseller.get("level", 0),
            "parent_id": reseller.get("parent_id")
        },
        reseller_id=reseller["id"]
    )

# List all resellers with hierarchy (admin/reseller)
@reseller_router.get("")
async def list_resellers(current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Admin pode ver todas
    if current_user["user_type"] == "admin":
        resellers = await db.resellers.find({}, {"_id": 0, "pass_hash": 0}).to_list(None)
    # Reseller pode ver apenas suas sub-revendas
    elif current_user["user_type"] == "reseller":
        resellers = await db.resellers.find(
            {"parent_id": current_user["user_id"]},
            {"_id": 0, "pass_hash": 0}
        ).to_list(None)
    else:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Adicionar contagem de filhos
    for reseller in resellers:
        reseller["children_count"] = await count_children(reseller["id"], db)
    
    return resellers

# Get reseller hierarchy tree (admin only)
@reseller_router.get("/hierarchy")
async def get_hierarchy(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
    async def build_tree(parent_id: Optional[str] = None) -> List[dict]:
        """Constrói árvore hierárquica recursivamente"""
        resellers = await db.resellers.find(
            {"parent_id": parent_id},
            {"_id": 0, "pass_hash": 0}
        ).to_list(None)
        
        tree = []
        for reseller in resellers:
            reseller["children"] = await build_tree(reseller["id"])
            reseller["children_count"] = len(reseller["children"])
            tree.append(reseller)
        
        return tree
    
    # Começar da raiz (parent_id = None)
    hierarchy = await build_tree(None)
    return {"hierarchy": hierarchy}

# Get single reseller details
@reseller_router.get("/{reseller_id}")
async def get_reseller(reseller_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Admin pode ver qualquer uma
    if current_user["user_type"] == "admin":
        reseller = await db.resellers.find_one({"id": reseller_id}, {"_id": 0, "pass_hash": 0})
    # Reseller pode ver apenas ela mesma ou suas filhas
    elif current_user["user_type"] == "reseller":
        reseller = await db.resellers.find_one({
            "$or": [
                {"id": reseller_id, "id": current_user["user_id"]},  # Ela mesma
                {"id": reseller_id, "parent_id": current_user["user_id"]}  # Sua filha
            ]
        }, {"_id": 0, "pass_hash": 0})
    else:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    if not reseller:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    reseller["children_count"] = await count_children(reseller["id"], db)
    return reseller

# Create reseller (admin/reseller)
@reseller_router.post("")
async def create_reseller(data: ResellerCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Determinar parent_id baseado em quem está criando
    parent_id = data.parent_id
    
    if current_user["user_type"] == "admin":
        # Admin pode criar revenda raiz ou com qualquer parent
        pass
    elif current_user["user_type"] == "reseller":
        # Reseller só pode criar sub-revendas com ela mesma como pai
        parent_id = current_user["user_id"]
    else:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Check if email exists
    existing = await db.resellers.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Calcular nível
    level = await calculate_level(parent_id, db)
    
    reseller_id = str(uuid.uuid4())
    pass_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    reseller = {
        "id": reseller_id,
        "name": data.name,
        "email": data.email,
        "pass_hash": pass_hash,
        "domain": data.domain or "",
        "custom_domain": "",
        "is_active": True,
        "parent_id": parent_id,
        "level": level,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.resellers.insert_one(reseller)
    
    # Create default config for reseller
    config = {
        "id": f"config_{reseller_id}",
        "reseller_id": reseller_id,
        "quick_blocks": [],
        "auto_reply": [],
        "apps": []
    }
    await db.reseller_configs.insert_one(config)
    
    logger.info(f"Reseller created: {data.name} (Level: {level}, Parent: {parent_id})")
    
    return {"ok": True, "reseller_id": reseller_id, "level": level}

# Update reseller
@reseller_router.put("/{reseller_id}")
async def update_reseller(reseller_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Admin pode atualizar qualquer uma
    if current_user["user_type"] == "admin":
        pass
    # Revendedor só pode atualizar seus próprios dados
    elif current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    else:
        if current_user["user_type"] != "reseller":
            raise HTTPException(status_code=403, detail="Não autorizado")
    
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "custom_domain" in data:
        update_data["custom_domain"] = data["custom_domain"]
    if "is_active" in data and current_user["user_type"] == "admin":
        update_data["is_active"] = data["is_active"]
    if "password" in data and data["password"]:
        update_data["pass_hash"] = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    
    if update_data:
        await db.resellers.update_one({"id": reseller_id}, {"$set": update_data})
    
    return {"ok": True}

# Transfer reseller to new parent (admin only)
@reseller_router.post("/transfer")
async def transfer_reseller(data: ResellerTransfer, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas Admin Master pode transferir revendas")
    
    db = get_db_dep()
    
    # Buscar revenda
    reseller = await db.resellers.find_one({"id": data.reseller_id})
    if not reseller:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    # Validar novo pai (se não for None)
    if data.new_parent_id:
        new_parent = await db.resellers.find_one({"id": data.new_parent_id})
        if not new_parent:
            raise HTTPException(status_code=404, detail="Nova revenda pai não encontrada")
        
        # Não pode ser filha de si mesma
        if data.new_parent_id == data.reseller_id:
            raise HTTPException(status_code=400, detail="Revenda não pode ser filha de si mesma")
    
    # Calcular novo nível
    new_level = await calculate_level(data.new_parent_id, db)
    
    # Atualizar revenda
    await db.resellers.update_one(
        {"id": data.reseller_id},
        {"$set": {
            "parent_id": data.new_parent_id,
            "level": new_level
        }}
    )
    
    # Atualizar níveis de todas as sub-revendas recursivamente
    async def update_children_levels(parent_id: str, base_level: int):
        children = await db.resellers.find({"parent_id": parent_id}).to_list(None)
        for child in children:
            new_child_level = base_level + 1
            await db.resellers.update_one(
                {"id": child["id"]},
                {"$set": {"level": new_child_level}}
            )
            await update_children_levels(child["id"], new_child_level)
    
    await update_children_levels(data.reseller_id, new_level)
    
    logger.info(f"Reseller transferred: {reseller['name']} -> New Parent: {data.new_parent_id}")
    
    return {"ok": True, "message": "Revenda transferida com sucesso"}

# Delete reseller (admin only - with children check)
@reseller_router.delete("/{reseller_id}")
async def delete_reseller(reseller_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
    # Verificar se pode deletar
    can_delete, message = await can_delete_reseller(reseller_id, db)
    if not can_delete:
        raise HTTPException(status_code=400, detail=message)
    
    # Deletar revenda e configs
    await db.resellers.delete_one({"id": reseller_id})
    await db.reseller_configs.delete_one({"reseller_id": reseller_id})
    
    # Deletar todos os dados associados (isolamento)
    await db.agents.delete_many({"reseller_id": reseller_id})
    await db.users.delete_many({"reseller_id": reseller_id})
    await db.tickets.delete_many({"reseller_id": reseller_id})
    await db.messages.delete_many({"reseller_id": reseller_id})
    await db.notices.delete_many({"reseller_id": reseller_id})
    
    logger.info(f"Reseller deleted: {reseller_id}")
    
    return {"ok": True, "message": "Revenda deletada com sucesso"}

# Get reseller config
@reseller_router.get("/{reseller_id}/config")
async def get_reseller_config(reseller_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Validar acesso
    if current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    config = await db.reseller_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    if not config:
        config = {
            "id": f"config_{reseller_id}",
            "reseller_id": reseller_id,
            "quick_blocks": [],
            "auto_reply": [],
            "apps": []
        }
        await db.reseller_configs.insert_one(config)
    
    return config

# Update reseller config
@reseller_router.put("/{reseller_id}/config")
async def update_reseller_config(reseller_id: str, data: ConfigData, current_user: dict = Depends(get_current_user)):
    db = get_db_dep()
    
    # Admin ou a própria revenda
    if current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    await db.reseller_configs.update_one(
        {"reseller_id": reseller_id},
        {"$set": {
            "quick_blocks": [b.dict() for b in data.quick_blocks],
            "auto_reply": [a.dict() for a in data.auto_reply],
            "apps": [app.dict() for app in data.apps]
        }},
        upsert=True
    )
    
    return {"ok": True}

# Replicate main config to all resellers (admin only)
@reseller_router.post("/replicate-config")
async def replicate_config_to_resellers(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
    # Get main config
    main_config = await db.config.find_one({"id": "config"})
    if not main_config:
        return {"ok": False, "message": "Configuração principal não encontrada"}
    
    # Get all resellers
    resellers = await db.resellers.find({}, {"id": 1}).to_list(None)
    
    updated_count = 0
    for reseller in resellers:
        await db.reseller_configs.update_one(
            {"reseller_id": reseller["id"]},
            {"$set": {
                "quick_blocks": main_config.get("quick_blocks", []),
                "auto_reply": main_config.get("auto_reply", []),
                "apps": main_config.get("apps", [])
            }},
            upsert=True
        )
        updated_count += 1
    
    logger.info(f"Config replicated to {updated_count} resellers")
    
    return {"ok": True, "updated": updated_count, "message": f"Configuração replicada para {updated_count} revenda(s)"}
