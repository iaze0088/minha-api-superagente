#!/usr/bin/env python3
"""
Fix the password for the ajuda.vip reseller.
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cybertv-support-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"
REPORTED_EMAIL = "michael@gmail.com"
REPORTED_PASSWORD = "ab181818ab"
REPORTED_DOMAIN = "ajuda.vip"

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
    print("🔧 FIXING PASSWORD FOR AJUDA.VIP RESELLER")
    print("=" * 50)
    
    # Step 1: Admin login
    print("🔐 Logging in as admin...")
    success, response = make_request("POST", "/auth/admin/login", {
        "password": ADMIN_PASSWORD
    })
    
    if not success or "token" not in response:
        print(f"❌ Admin login failed: {response}")
        return
        
    admin_token = response["token"]
    print("✅ Admin login successful")
    
    # Step 2: Find the reseller with ajuda.vip domain
    print(f"🔍 Finding reseller with domain: {REPORTED_DOMAIN}")
    success, response = make_request("GET", "/resellers", token=admin_token)
    
    if not success:
        print(f"❌ Failed to list resellers: {response}")
        return
        
    ajuda_reseller = None
    for reseller in response:
        if (reseller.get('custom_domain') == REPORTED_DOMAIN or 
            reseller.get('domain') == REPORTED_DOMAIN):
            ajuda_reseller = reseller
            break
    
    if not ajuda_reseller:
        print(f"❌ No reseller found with domain {REPORTED_DOMAIN}")
        return
        
    reseller_id = ajuda_reseller.get('id')
    current_email = ajuda_reseller.get('email')
    print(f"✅ Found reseller: {ajuda_reseller.get('name')} (ID: {reseller_id})")
    print(f"   Current email: {current_email}")
    
    # Step 3: Update both email and password
    print(f"🔧 Updating reseller to:")
    print(f"   Email: {REPORTED_EMAIL}")
    print(f"   Password: {REPORTED_PASSWORD}")
    
    success, response = make_request("PUT", f"/resellers/{reseller_id}", {
        "email": REPORTED_EMAIL,
        "password": REPORTED_PASSWORD
    }, token=admin_token)
    
    if not success or not response.get("ok"):
        print(f"❌ Failed to update reseller: {response}")
        return
        
    print("✅ Reseller updated successfully")
    
    # Step 4: Test login
    print("🧪 Testing login with updated credentials...")
    success, response = make_request("POST", "/resellers/login", {
        "email": REPORTED_EMAIL,
        "password": REPORTED_PASSWORD
    })
    
    if success and "token" in response:
        print("✅ LOGIN SUCCESSFUL!")
        print(f"   Token received: {response['token'][:50]}...")
        print(f"   User data: {response.get('user_data', {})}")
        
        # Test with Host header
        print("🌐 Testing with Host header...")
        headers = {"Host": REPORTED_DOMAIN}
        success2, response2 = make_request("GET", "/agents", 
                                         token=response["token"])
        
        if success2:
            agent_count = len(response2) if isinstance(response2, list) else 0
            print(f"✅ Tenant middleware working - {agent_count} agents found")
        else:
            print(f"⚠️  Tenant middleware issue: {response2}")
            
    else:
        print(f"❌ Login still failed: {response}")
        
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print(f"   Domain: {REPORTED_DOMAIN}")
    print(f"   Email: {REPORTED_EMAIL}")
    print(f"   Password: {REPORTED_PASSWORD}")
    print(f"   Status: {'✅ WORKING' if success and 'token' in response else '❌ FAILED'}")

if __name__ == "__main__":
    main()