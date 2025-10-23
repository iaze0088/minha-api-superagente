"""
Middleware para detecção automática de tenant (reseller) baseado no domínio da requisição.
"""
from fastapi import Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TenantContext:
    """Contexto do tenant atual da requisição"""
    def __init__(self):
        self.reseller_id: Optional[str] = None
        self.reseller_data: Optional[dict] = None
        self.is_master: bool = False

# Global tenant context (thread-safe via FastAPI's request context)
tenant_context = TenantContext()

async def get_tenant_from_domain(domain: str, db: AsyncIOMotorDatabase) -> Optional[dict]:
    """
    Busca a revenda (tenant) pelo domínio customizado OU domínio de teste.
    
    Args:
        domain: Domínio da requisição (ex: ajuda.vip, reseller-xxx.preview.emergentagent.com)
        db: Instância do banco MongoDB
        
    Returns:
        Dados da revenda ou None se não encontrar
    """
    if not domain:
        return None
    
    # Remove www. se existir
    domain = domain.replace("www.", "")
    
    # Busca revenda pelo custom_domain OU test_domain (com test_domain_active)
    reseller = await db.resellers.find_one({
        "$or": [
            {"custom_domain": domain},
            {"test_domain": domain, "test_domain_active": True}
        ],
        "is_active": True
    })
    
    return reseller

async def detect_tenant(request: Request, db: AsyncIOMotorDatabase) -> TenantContext:
    """
    Detecta o tenant atual baseado no domínio da requisição.
    
    Args:
        request: Objeto Request do FastAPI
        db: Instância do banco MongoDB
        
    Returns:
        TenantContext com informações do tenant
    """
    context = TenantContext()
    
    # Pega o host da requisição
    host = request.headers.get("host", "")
    domain = host.split(":")[0]  # Remove porta se existir
    
    logger.info(f"Detecting tenant for domain: {domain}")
    
    # Domínios master (admin principal)
    master_domains = [
        "suporte.help",
        "localhost",
        "127.0.0.1"
    ]
    
    # Verifica se é domínio master
    if any(master in domain for master in master_domains):
        context.is_master = True
        context.reseller_id = None
        logger.info("Master domain detected")
        return context
    
    # Busca revenda pelo domínio
    reseller = await get_tenant_from_domain(domain, db)
    
    if reseller:
        context.reseller_id = reseller["id"]
        context.reseller_data = reseller
        context.is_master = False
        logger.info(f"Tenant detected: {reseller['name']} (ID: {reseller['id']})")
    else:
        # Se não encontrou revenda mas não é master, pode ser um domínio não configurado
        logger.warning(f"No tenant found for domain: {domain}")
        context.is_master = False
        context.reseller_id = None
    
    return context

def get_current_tenant() -> TenantContext:
    """
    Retorna o contexto do tenant atual.
    Use isso em rotas que precisam acessar o tenant.
    """
    return tenant_context

async def apply_tenant_filter(filter_dict: dict, tenant_context: TenantContext, 
                               allow_master_access: bool = False) -> dict:
    """
    Aplica filtro de tenant em queries do MongoDB.
    
    Args:
        filter_dict: Filtro original da query
        tenant_context: Contexto do tenant atual
        allow_master_access: Se True, admin master pode ver todos os dados
        
    Returns:
        Filtro com restrição de tenant aplicada
    """
    if tenant_context.is_master and allow_master_access:
        # Admin master pode ver tudo se allow_master_access=True
        return filter_dict
    
    if tenant_context.reseller_id:
        # Adiciona filtro de reseller_id
        filter_dict["reseller_id"] = tenant_context.reseller_id
    
    return filter_dict

async def validate_tenant_access(reseller_id: str, tenant_context: TenantContext) -> bool:
    """
    Valida se o tenant atual tem acesso a um recurso específico.
    
    Args:
        reseller_id: ID da revenda do recurso
        tenant_context: Contexto do tenant atual
        
    Returns:
        True se tem acesso, False caso contrário
    """
    # Admin master tem acesso a tudo
    if tenant_context.is_master:
        return True
    
    # Verifica se o reseller_id do recurso pertence ao tenant atual
    if tenant_context.reseller_id == reseller_id:
        return True
    
    return False
