#!/usr/bin/env python3
"""
Fix ajuda.vip reseller email to match expected credentials
"""

import requests
import json
import os
import bcrypt

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://reseller-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"

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
    print("🔧 CORRIGINDO EMAIL DA REVENDA AJUDA.VIP")
    print("=" * 50)
    
    # Login as admin
    success, response = make_request("POST", "/auth/admin/login", {
        "password": ADMIN_PASSWORD
    })
    
    if not success or "token" not in response:
        print(f"❌ Erro no login admin: {response}")
        return
    
    admin_token = response["token"]
    print("✅ Login admin realizado com sucesso")
    
    # Get all resellers
    success, resellers = make_request("GET", "/resellers", token=admin_token)
    
    if not success:
        print(f"❌ Erro ao listar revendas: {resellers}")
        return
    
    # Find ajuda.vip reseller
    ajuda_reseller = None
    for reseller in resellers:
        if reseller.get('custom_domain') == 'ajuda.vip':
            ajuda_reseller = reseller
            break
    
    if not ajuda_reseller:
        print("❌ Revenda ajuda.vip não encontrada")
        return
    
    print(f"📋 Revenda encontrada:")
    print(f"   ID: {ajuda_reseller['id']}")
    print(f"   Nome: {ajuda_reseller['name']}")
    print(f"   Email atual: {ajuda_reseller['email']}")
    print(f"   Custom Domain: {ajuda_reseller['custom_domain']}")
    
    # Update email and password
    update_data = {
        "email": "michaelrv@gmail.com",
        "password": "ab181818ab"
    }
    
    print(f"\n🔄 Atualizando para:")
    print(f"   Email: {update_data['email']}")
    print(f"   Senha: {update_data['password']}")
    
    success, response = make_request("PUT", f"/resellers/{ajuda_reseller['id']}", 
                                   update_data, admin_token)
    
    if success and response.get("ok"):
        print("✅ Revenda atualizada com sucesso!")
        
        # Test login
        login_data = {
            "email": "michaelrv@gmail.com",
            "password": "ab181818ab"
        }
        
        print(f"\n🔐 Testando login...")
        success, login_response = make_request("POST", "/resellers/login", login_data)
        
        if success and "token" in login_response:
            print("🎉 LOGIN FUNCIONANDO!")
            print(f"   Email: {login_data['email']}")
            print(f"   Senha: {login_data['password']}")
            print(f"   Reseller ID: {login_response.get('reseller_id')}")
            print(f"   Token: {login_response.get('token', '')[:50]}...")
        else:
            print(f"❌ Login ainda não funciona: {login_response}")
    else:
        print(f"❌ Erro ao atualizar revenda: {response}")

if __name__ == "__main__":
    main()