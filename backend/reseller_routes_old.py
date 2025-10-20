import os
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from models import *
import jwt

reseller_router = APIRouter(prefix="/api/resellers", tags=["resellers"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key-change-in-production')

def create_token(user_id: str, user_type: str) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
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

# Reseller authentication
@reseller_router.post("/login")
async def reseller_login(data: ResellerLogin):
    db = get_db_dep()
    reseller = await db.resellers.find_one({"email": data.email})
    if not reseller or not bcrypt.checkpw(data.password.encode(), reseller["pass_hash"].encode()):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    if not reseller.get("is_active", True):
        raise HTTPException(status_code=403, detail="Revenda desativada")
    
    token = create_token(reseller["id"], "reseller")
    
    return TokenResponse(
        token=token,
        user_type="reseller",
        user_data={
            "id": reseller["id"],
            "name": reseller["name"],
            "email": reseller["email"],
            "domain": reseller.get("domain", ""),
            "custom_domain": reseller.get("custom_domain", "")
        },
        reseller_id=reseller["id"]
    )

# List all resellers (admin only)
@reseller_router.get("")
async def list_resellers(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    resellers = await db.resellers.find({}, {"_id": 0, "pass_hash": 0}).to_list(None)
    return resellers

# Create reseller (admin only)
@reseller_router.post("")
async def create_reseller(data: ResellerCreate, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
    # Check if email exists
    existing = await db.resellers.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
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
    
    return {"ok": True, "reseller_id": reseller_id}

# Update reseller
@reseller_router.put("/{reseller_id}")
async def update_reseller(reseller_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Revendedor só pode atualizar seus próprios dados
    if current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
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

# Delete reseller (admin only)
@reseller_router.delete("/{reseller_id}")
async def delete_reseller(reseller_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
    await db.resellers.delete_one({"id": reseller_id})
    await db.reseller_configs.delete_one({"reseller_id": reseller_id})
    
    return {"ok": True}

# Get reseller config
@reseller_router.get("/{reseller_id}/config")
async def get_reseller_config(reseller_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
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
    if current_user["user_type"] == "reseller" and current_user["user_id"] != reseller_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db = get_db_dep()
    
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
    
    return {"ok": True, "updated": updated_count, "message": f"Configuração replicada para {updated_count} revenda(s)"}
