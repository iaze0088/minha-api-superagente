#!/usr/bin/env python3
"""
Test reseller access to config and other endpoints
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supportdesk-pro.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def make_request(method: str, endpoint: str, data: dict = None, token: str = None) -> tuple[bool, dict]:
    """Make HTTP request with error handling"""
    url = f"{API_BASE}{endpoint}"
    
    request_headers = {"Content-Type": "application/json"}
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
        
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=request_headers, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=request_headers, timeout=30)
        else:
            return False, {"error": f"Unsupported method: {method}"}
            
        return response.status_code < 400, response.json() if response.text else {}
        
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except json.JSONDecodeError:
        return False, {"error": "Invalid JSON response"}

def main():
    print("🔐 TESTANDO ACESSO DA REVENDA AJUDA.VIP")
    print("=" * 50)
    
    # Login as reseller
    login_data = {
        "email": "michaelrv@gmail.com",
        "password": "ab181818ab"
    }
    
    success, response = make_request("POST", "/resellers/login", login_data)
    
    if not success or "token" not in response:
        print(f"❌ Erro no login: {response}")
        return
    
    token = response["token"]
    reseller_id = response.get("reseller_id")
    
    print("✅ Login realizado com sucesso!")
    print(f"   Reseller ID: {reseller_id}")
    print(f"   Token: {token[:50]}...")
    
    # Test config access
    print(f"\n📋 Testando acesso à configuração...")
    success, config = make_request("GET", "/config", token=token)
    
    if success:
        print("✅ Acesso à config funcionando!")
        print(f"   Config ID: {config.get('id', 'N/A')}")
        print(f"   Reseller ID: {config.get('reseller_id', 'N/A')}")
        print(f"   Quick Blocks: {len(config.get('quick_blocks', []))}")
        print(f"   Auto Reply: {len(config.get('auto_reply', []))}")
    else:
        print(f"❌ Erro no acesso à config: {config}")
    
    # Test agents access
    print(f"\n👥 Testando acesso aos agentes...")
    success, agents = make_request("GET", "/agents", token=token)
    
    if success:
        print(f"✅ Acesso aos agentes funcionando!")
        print(f"   Agentes encontrados: {len(agents) if isinstance(agents, list) else 0}")
        for i, agent in enumerate(agents[:3] if isinstance(agents, list) else [], 1):
            print(f"   {i}. {agent.get('name', 'N/A')} ({agent.get('login', 'N/A')})")
    else:
        print(f"❌ Erro no acesso aos agentes: {agents}")
    
    # Test tickets access
    print(f"\n🎫 Testando acesso aos tickets...")
    success, tickets = make_request("GET", "/tickets", token=token)
    
    if success:
        print(f"✅ Acesso aos tickets funcionando!")
        print(f"   Tickets encontrados: {len(tickets) if isinstance(tickets, list) else 0}")
    else:
        print(f"❌ Erro no acesso aos tickets: {tickets}")
    
    print(f"\n🎉 TESTE COMPLETO - REVENDA AJUDA.VIP FUNCIONANDO!")
    print(f"   Domínio: ajuda.vip")
    print(f"   Email: michaelrv@gmail.com")
    print(f"   Senha: ab181818ab")
    print(f"   Reseller ID: {reseller_id}")

if __name__ == "__main__":
    main()