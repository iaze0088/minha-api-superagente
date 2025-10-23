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
    tenant = get_request_tenant(request)
    query = {}
    
    if not current_user:
        return query
    
    user_type = current_user.get("user_type")
    
    # Admin master vê TUDO (sem filtro)
    if user_type == "admin" and tenant.is_master:
        return query
    
    # Admin acessando via domínio de revenda específica
    if user_type == "admin" and tenant.reseller_id:
        query["reseller_id"] = tenant.reseller_id
        return query
    
    # Reseller vê APENAS seus dados
    if user_type == "reseller":
        reseller_id = current_user.get("reseller_id")
        if reseller_id:
            query["reseller_id"] = reseller_id
        return query
    
    # Agent vê APENAS dados da sua revenda
    if user_type == "agent":
        reseller_id = current_user.get("reseller_id")
        if reseller_id:
            query["reseller_id"] = reseller_id
        return query
    
    # Client vê dados da revenda atual
    if user_type == "client":
        if tenant.reseller_id:
            query["reseller_id"] = tenant.reseller_id
        return query
    
    return query
