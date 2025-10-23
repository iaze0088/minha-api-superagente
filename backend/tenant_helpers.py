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
    
    REGRA: Agent/Reseller veem APENAS seus dados pelo reseller_id do TOKEN
    """
    tenant = get_request_tenant(request)
    query = {}
    
    if not current_user:
        return query
    
    user_type = current_user.get("user_type")
    user_reseller_id = current_user.get("reseller_id")
    
    # Admin master vê TUDO (sem filtro)
    if user_type == "admin" and tenant.is_master:
        return query
    
    # Admin via domínio de revenda: filtra por tenant
    if user_type == "admin" and tenant.reseller_id:
        query["reseller_id"] = tenant.reseller_id
        return query
    
    # Reseller/Agent: SEMPRE filtram pelo reseller_id do TOKEN
    if user_type in ["reseller", "agent"]:
        if user_reseller_id:
            query["reseller_id"] = user_reseller_id
        return query
    
    # Client: filtra pelo tenant do request
    if user_type == "client":
        if tenant.reseller_id:
            query["reseller_id"] = tenant.reseller_id
        return query
    
    return query
