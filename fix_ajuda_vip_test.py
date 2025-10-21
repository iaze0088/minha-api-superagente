#!/usr/bin/env python3
"""
Fix the ajuda.vip domain login issue.
This script will identify and fix the problem.
"""

import requests
import json
import os
import bcrypt
from typing import Dict, Optional, List

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cyberchat-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from the issue
ADMIN_PASSWORD = "102030@ab"
REPORTED_EMAIL = "michael@gmail.com"
REPORTED_PASSWORD = "ab181818ab"
REPORTED_DOMAIN = "ajuda.vip"

class AjudaVipFixer:
    def __init__(self):
        self.admin_token = None
        self.ajuda_vip_reseller = None
        
    def log(self, message: str):
        """Log message"""
        print(f"🔧 {message}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    token: str = None, headers: dict = None) -> tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            return response.status_code < 400, response.json() if response.text else {}
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}
            
    def admin_login(self) -> bool:
        """Login as admin"""
        self.log(f"Logging in as admin with password: {ADMIN_PASSWORD}")
        
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log("✅ Admin login successful")
            return True
        else:
            self.log(f"❌ Admin login failed: {response}")
            return False
            
    def find_ajuda_vip_reseller(self) -> Optional[Dict]:
        """Find the reseller with ajuda.vip domain"""
        self.log(f"Finding reseller with domain: {REPORTED_DOMAIN}")
        
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            for reseller in response:
                if (reseller.get('custom_domain') == REPORTED_DOMAIN or 
                    reseller.get('domain') == REPORTED_DOMAIN):
                    
                    self.log(f"✅ Found reseller: {reseller.get('name')} ({reseller.get('email')})")
                    self.ajuda_vip_reseller = reseller
                    return reseller
            
            self.log(f"❌ No reseller found with domain {REPORTED_DOMAIN}")
            return None
        else:
            self.log(f"❌ Error listing resellers: {response}")
            return None
            
    def test_current_login(self) -> bool:
        """Test login with current reseller email and reported password"""
        if not self.ajuda_vip_reseller:
            return False
            
        current_email = self.ajuda_vip_reseller.get('email')
        self.log(f"Testing login with current email: {current_email}")
        
        success, response = self.make_request("POST", "/resellers/login", {
            "email": current_email,
            "password": REPORTED_PASSWORD
        })
        
        if success and "token" in response:
            self.log(f"✅ Login successful with current email: {current_email}")
            return True
        else:
            self.log(f"❌ Login failed with current email: {response}")
            return False
            
    def test_reported_email_login(self) -> bool:
        """Test login with reported email"""
        self.log(f"Testing login with reported email: {REPORTED_EMAIL}")
        
        success, response = self.make_request("POST", "/resellers/login", {
            "email": REPORTED_EMAIL,
            "password": REPORTED_PASSWORD
        })
        
        if success and "token" in response:
            self.log(f"✅ Login successful with reported email: {REPORTED_EMAIL}")
            return True
        else:
            self.log(f"❌ Login failed with reported email: {response}")
            return False
            
    def check_if_michael_reseller_exists(self) -> Optional[Dict]:
        """Check if there's a reseller with michael@gmail.com email"""
        self.log(f"Checking if reseller exists with email: {REPORTED_EMAIL}")
        
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            for reseller in response:
                if reseller.get('email') == REPORTED_EMAIL:
                    self.log(f"✅ Found reseller with email {REPORTED_EMAIL}: {reseller.get('name')}")
                    return reseller
            
            self.log(f"❌ No reseller found with email {REPORTED_EMAIL}")
            return None
        else:
            self.log(f"❌ Error listing resellers: {response}")
            return None
            
    def fix_option_1_update_email(self) -> bool:
        """Fix Option 1: Update the ajuda.vip reseller email to michael@gmail.com"""
        if not self.ajuda_vip_reseller:
            return False
            
        reseller_id = self.ajuda_vip_reseller.get('id')
        self.log(f"FIX OPTION 1: Updating reseller {reseller_id} email to {REPORTED_EMAIL}")
        
        # First check if email is already taken
        michael_reseller = self.check_if_michael_reseller_exists()
        if michael_reseller and michael_reseller.get('id') != reseller_id:
            self.log(f"❌ Cannot update email - {REPORTED_EMAIL} is already used by another reseller")
            return False
        
        success, response = self.make_request("PUT", f"/resellers/{reseller_id}", {
            "email": REPORTED_EMAIL
        }, token=self.admin_token)
        
        if success and response.get("ok"):
            self.log(f"✅ Email updated successfully to {REPORTED_EMAIL}")
            return True
        else:
            self.log(f"❌ Failed to update email: {response}")
            return False
            
    def fix_option_2_update_password(self) -> bool:
        """Fix Option 2: Update the ajuda.vip reseller password to match reported password"""
        if not self.ajuda_vip_reseller:
            return False
            
        reseller_id = self.ajuda_vip_reseller.get('id')
        self.log(f"FIX OPTION 2: Updating reseller {reseller_id} password to {REPORTED_PASSWORD}")
        
        success, response = self.make_request("PUT", f"/resellers/{reseller_id}", {
            "password": REPORTED_PASSWORD
        }, token=self.admin_token)
        
        if success and response.get("ok"):
            self.log(f"✅ Password updated successfully")
            return True
        else:
            self.log(f"❌ Failed to update password: {response}")
            return False
            
    def fix_option_3_update_michael_domain(self) -> bool:
        """Fix Option 3: Update michael@gmail.com reseller to have ajuda.vip domain"""
        michael_reseller = self.check_if_michael_reseller_exists()
        if not michael_reseller:
            self.log(f"❌ No reseller found with email {REPORTED_EMAIL}")
            return False
            
        michael_id = michael_reseller.get('id')
        self.log(f"FIX OPTION 3: Updating reseller {michael_id} custom_domain to {REPORTED_DOMAIN}")
        
        # First remove domain from current ajuda.vip reseller
        if self.ajuda_vip_reseller:
            current_id = self.ajuda_vip_reseller.get('id')
            self.log(f"Removing domain from current reseller {current_id}")
            
            success, response = self.make_request("PUT", f"/resellers/{current_id}", {
                "custom_domain": ""
            }, token=self.admin_token)
            
            if not success:
                self.log(f"❌ Failed to remove domain from current reseller: {response}")
                return False
        
        # Now add domain to michael's reseller
        success, response = self.make_request("PUT", f"/resellers/{michael_id}", {
            "custom_domain": REPORTED_DOMAIN,
            "password": REPORTED_PASSWORD  # Also update password
        }, token=self.admin_token)
        
        if success and response.get("ok"):
            self.log(f"✅ Domain and password updated successfully for {REPORTED_EMAIL}")
            return True
        else:
            self.log(f"❌ Failed to update domain: {response}")
            return False
            
    def verify_fix(self) -> bool:
        """Verify that the fix worked"""
        self.log("Verifying the fix...")
        
        # Test login with reported credentials
        success, response = self.make_request("POST", "/resellers/login", {
            "email": REPORTED_EMAIL,
            "password": REPORTED_PASSWORD
        })
        
        if success and "token" in response:
            self.log(f"✅ FIX VERIFIED: Login successful with {REPORTED_EMAIL} / {REPORTED_PASSWORD}")
            
            # Also test with Host header to simulate ajuda.vip access
            headers = {"Host": REPORTED_DOMAIN}
            success2, response2 = self.make_request("GET", "/agents", 
                                                  headers=headers, token=response["token"])
            
            if success2:
                self.log(f"✅ Tenant middleware also working with Host: {REPORTED_DOMAIN}")
            else:
                self.log(f"⚠️  Tenant middleware issue: {response2}")
            
            return True
        else:
            self.log(f"❌ FIX FAILED: Login still not working: {response}")
            return False
            
    def run_diagnosis_and_fix(self):
        """Run complete diagnosis and fix"""
        print("🚀 AJUDA.VIP LOGIN ISSUE - DIAGNOSIS AND FIX")
        print("=" * 60)
        
        # Step 1: Admin login
        if not self.admin_login():
            print("❌ Cannot proceed without admin access")
            return
            
        # Step 2: Find ajuda.vip reseller
        ajuda_reseller = self.find_ajuda_vip_reseller()
        
        # Step 3: Check if michael@gmail.com reseller exists
        michael_reseller = self.check_if_michael_reseller_exists()
        
        # Step 4: Test current login scenarios
        current_login_works = self.test_current_login()
        reported_login_works = self.test_reported_email_login()
        
        print("\n" + "=" * 60)
        print("📊 DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        if ajuda_reseller:
            print(f"✅ Reseller with domain {REPORTED_DOMAIN} found:")
            print(f"   Email: {ajuda_reseller.get('email')}")
            print(f"   Name: {ajuda_reseller.get('name')}")
        else:
            print(f"❌ No reseller found with domain {REPORTED_DOMAIN}")
            
        if michael_reseller:
            print(f"✅ Reseller with email {REPORTED_EMAIL} found:")
            print(f"   Name: {michael_reseller.get('name')}")
            print(f"   Domain: {michael_reseller.get('domain')}")
            print(f"   Custom Domain: {michael_reseller.get('custom_domain')}")
        else:
            print(f"❌ No reseller found with email {REPORTED_EMAIL}")
            
        print(f"Current reseller login works: {'✅' if current_login_works else '❌'}")
        print(f"Reported email login works: {'✅' if reported_login_works else '❌'}")
        
        # Determine best fix strategy
        print("\n" + "=" * 60)
        print("🔧 APPLYING FIX")
        print("=" * 60)
        
        fix_applied = False
        
        if ajuda_reseller and michael_reseller:
            # Both exist - transfer domain to michael's account
            self.log("Strategy: Transfer ajuda.vip domain to michael@gmail.com account")
            fix_applied = self.fix_option_3_update_michael_domain()
            
        elif ajuda_reseller and not michael_reseller:
            # Only ajuda.vip reseller exists - update its email
            self.log("Strategy: Update ajuda.vip reseller email to michael@gmail.com")
            fix_applied = self.fix_option_1_update_email()
            if not fix_applied:
                # Try updating password instead
                self.log("Strategy: Update ajuda.vip reseller password")
                fix_applied = self.fix_option_2_update_password()
                
        elif not ajuda_reseller and michael_reseller:
            # Only michael exists - add domain to his account
            self.log("Strategy: Add ajuda.vip domain to michael@gmail.com account")
            michael_id = michael_reseller.get('id')
            success, response = self.make_request("PUT", f"/resellers/{michael_id}", {
                "custom_domain": REPORTED_DOMAIN,
                "password": REPORTED_PASSWORD
            }, token=self.admin_token)
            fix_applied = success and response.get("ok")
            
        else:
            # Neither exists - create new reseller
            self.log("Strategy: Create new reseller for michael@gmail.com with ajuda.vip domain")
            success, response = self.make_request("POST", "/resellers", {
                "name": "Michael Reseller",
                "email": REPORTED_EMAIL,
                "password": REPORTED_PASSWORD,
                "domain": "",
                "parent_id": None
            }, token=self.admin_token)
            
            if success and response.get("ok"):
                reseller_id = response.get("reseller_id")
                # Add custom domain
                success2, response2 = self.make_request("PUT", f"/resellers/{reseller_id}", {
                    "custom_domain": REPORTED_DOMAIN
                }, token=self.admin_token)
                fix_applied = success2 and response2.get("ok")
            else:
                fix_applied = False
        
        # Verify fix
        if fix_applied:
            print("\n" + "=" * 60)
            print("✅ VERIFICATION")
            print("=" * 60)
            self.verify_fix()
        else:
            print("\n❌ FIX FAILED - Manual intervention required")

def main():
    """Main execution"""
    print(f"🔗 Backend URL: {API_BASE}")
    
    fixer = AjudaVipFixer()
    fixer.run_diagnosis_and_fix()

if __name__ == "__main__":
    main()