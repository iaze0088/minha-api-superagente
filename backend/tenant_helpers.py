"""
Funções auxiliares para isolamento multi-tenant
"""
from fastapi import Request
from typing import Optional


# Tenant helper
class Tenant:
    """Classe simples para representar informações de tenant"""
    def __init__(self, reseller_id: Optional[str] = None, is_master: bool = False):
        self.reseller_id = reseller_id
        self.is_master = is_master


def get_request_tenant(request: Request = None) -> Tenant:
    """Extrai informações de tenant do request"""
    if not request:
        return Tenant(reseller_id=None, is_master=True)
    
    tenant_info = getattr(request.state, "tenant", None)
    if tenant_info:
        return tenant_info
    
    return Tenant(reseller_id=None, is_master=True)


def get_tenant_filter(request: Request = None, current_user: dict = None) -> dict:
    """
    FUNÇÃO CRÍTICA DE SEGURANÇA: Retorna filtro de isolamento multi-tenant
    
    REGRA RIGOROSA: Cada painel vê APENAS seus próprios dados!
    - Admin master: vê todos (sem filtro)
    - Reseller: vê apenas seus dados (reseller_id)
    - Agent: vê apenas dados da sua revenda (reseller_id)
    - Client: vê apenas dados da revenda atual (reseller_id)
    
    NUNCA uma revenda/atendente pode ver dados de outra revenda!
    """
    import logging
    logger = logging.getLogger("tenant_filter")
    
    tenant = get_request_tenant(request)
    query = {}
    
    if not current_user:
        logger.warning("🔒 get_tenant_filter: current_user é None!")
        return query
    
    user_type = current_user.get("user_type")
    user_reseller_id = current_user.get("reseller_id")
    
    logger.info(f"🔒 get_tenant_filter: user_type={user_type}, user_reseller_id={user_reseller_id}, tenant.is_master={tenant.is_master}, tenant.reseller_id={tenant.reseller_id}")
    
    # Admin master vê TUDO (sem filtro)
    if user_type == "admin" and tenant.is_master:
        logger.info("🔒 Admin master - sem filtro (vê tudo)")
        return query
    
    # Admin acessando via domínio de revenda específica
    if user_type == "admin" and tenant.reseller_id:
        query["reseller_id"] = tenant.reseller_id
        logger.info(f"🔒 Admin via domínio de revenda - filtro: reseller_id={tenant.reseller_id}")
        return query
    
    # Reseller vê APENAS seus dados
    if user_type == "reseller":
        if user_reseller_id:
            query["reseller_id"] = user_reseller_id
            logger.info(f"🔒 Reseller - filtro: reseller_id={user_reseller_id}")
        else:
            logger.warning("🔒 Reseller sem reseller_id no token!")
        return query
    
    # Agent vê APENAS dados da sua revenda
    if user_type == "agent":
        if user_reseller_id:
            query["reseller_id"] = user_reseller_id
            logger.info(f"🔒 Agent - filtro: reseller_id={user_reseller_id}")
        else:
            logger.warning("🔒 Agent sem reseller_id no token!")
        return query
    
    # Client vê dados da revenda atual
    if user_type == "client":
        if tenant.reseller_id:
            query["reseller_id"] = tenant.reseller_id
            logger.info(f"🔒 Client - filtro: reseller_id={tenant.reseller_id}")
        return query
    
    logger.warning(f"🔒 get_tenant_filter: Nenhuma condição correspondeu! user_type={user_type}")
    return query
