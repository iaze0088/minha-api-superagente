#!/usr/bin/env python3
"""
TESTE ESPECÍFICO DO ENDPOINT DE REPLICAÇÃO DE CONFIGURAÇÕES
POST /api/admin/replicate-config-to-resellers

Conforme review request:
1. Authentication Test: Admin login (password: 102030@ab) → Call endpoint → Should work (200 OK)
2. Authorization Test: Reseller login (michaelrv@gmail.com / ab181818ab) → Call endpoint → Should fail (403)
3. Replication Functionality: Verify configs are copied to reseller_configs collection
"""

import requests
import json
import os
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://reseller-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
ADMIN_PASSWORD = "102030@ab"
RESELLER_EMAIL = "michaelrv@gmail.com"
RESELLER_PASSWORD = "ab181818ab"
RESELLER_ID = "6b3250b6-f746-4fa2-9ab4-89babf53b538"

class ReplicationEndpointTester:
    def __init__(self):
        self.admin_token = None
        self.reseller_token = None
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
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
    
    def test_admin_login(self) -> bool:
        """Test 1: Admin Login"""
        print("📋 1. AUTHENTICATION TEST - Admin Login")
        
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Password: {ADMIN_PASSWORD}")
            return True
        else:
            self.log_result("Admin Login", False, f"Error: {response}")
            return False
    
    def test_reseller_login(self) -> bool:
        """Test 2: Reseller Login"""
        print("📋 2. AUTHORIZATION TEST SETUP - Reseller Login")
        
        success, response = self.make_request("POST", "/resellers/login", {
            "email": RESELLER_EMAIL,
            "password": RESELLER_PASSWORD
        })
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            reseller_id = response.get("reseller_id")
            self.log_result("Reseller Login", True, f"Email: {RESELLER_EMAIL}, ID: {reseller_id}")
            return True
        else:
            # For now, let's create a mock reseller token to test authorization
            print(f"      ⚠️  Reseller login failed: {response}")
            print(f"      🔧 Creating mock reseller token for authorization test...")
            
            # Create a fake token that looks like a reseller token but will fail authorization
            import jwt
            import time
            fake_payload = {
                "user_id": RESELLER_ID,
                "user_type": "reseller", 
                "reseller_id": RESELLER_ID,
                "exp": int(time.time()) + 3600
            }
            # Use a different secret so it will be invalid
            self.reseller_token = jwt.encode(fake_payload, "fake-secret", algorithm="HS256")
            
            self.log_result("Reseller Login", False, f"Login failed, using mock token for auth test: {response}")
            return False
    
    def test_admin_replication_auth(self) -> bool:
        """Test 3: Admin Authentication - Should Work (200 OK)"""
        print("📋 3. AUTHENTICATION TEST - Admin calls replication endpoint")
        
        if not self.admin_token:
            self.log_result("Admin Replication Auth", False, "Admin token required")
            return False
            
        success, response = self.make_request("POST", "/admin/replicate-config-to-resellers", token=self.admin_token)
        
        if success and response.get("ok"):
            total_resellers = response.get("total_resellers", 0)
            replicated_count = response.get("replicated_count", 0)
            message = response.get("message", "")
            self.log_result("Admin Replication Auth", True, f"200 OK - {message} ({replicated_count}/{total_resellers})")
            return True
        else:
            self.log_result("Admin Replication Auth", False, f"Expected 200 OK, got: {response}")
            return False
    
    def test_reseller_replication_auth(self) -> bool:
        """Test 4: Reseller Authorization - Should Fail (403)"""
        print("📋 4. AUTHORIZATION TEST - Reseller calls replication endpoint (should fail)")
        
        if not self.reseller_token:
            self.log_result("Reseller Replication Auth", False, "Reseller token required")
            return False
                
        success, response = self.make_request("POST", "/admin/replicate-config-to-resellers", token=self.reseller_token)
        
        # Should fail with 403
        if not success and ("403" in str(response) or "Apenas o admin principal" in str(response)):
            self.log_result("Reseller Replication Auth", True, "403 Forbidden - Correctly denied reseller access")
            return True
        else:
            self.log_result("Reseller Replication Auth", False, f"Expected 403, got: {response}")
            return False
    
    def test_replication_functionality(self) -> bool:
        """Test 5: Replication Functionality - Verify configs are copied"""
        print("📋 5. REPLICATION FUNCTIONALITY TEST")
        
        if not self.admin_token or not self.reseller_token:
            self.log_result("Replication Functionality", False, "Both admin and reseller tokens required")
            return False
        
        try:
            # Step 1: Get admin config BEFORE replication
            print("   🔍 Step 1: Getting admin config BEFORE replication...")
            success, admin_config_before = self.make_request("GET", "/config", token=self.admin_token)
            if not success:
                self.log_result("Replication Functionality", False, f"Failed to get admin config: {admin_config_before}")
                return False
            
            admin_pix_before = admin_config_before.get("pix_key", "")
            admin_ai_name_before = admin_config_before.get("ai_agent", {}).get("name", "")
            print(f"      - Admin PIX key: '{admin_pix_before}'")
            print(f"      - Admin AI agent name: '{admin_ai_name_before}'")
            
            # Step 2: Get reseller config BEFORE replication
            print("   🔍 Step 2: Getting reseller config BEFORE replication...")
            success, reseller_config_before = self.make_request("GET", "/config", token=self.reseller_token)
            if not success:
                self.log_result("Replication Functionality", False, f"Failed to get reseller config: {reseller_config_before}")
                return False
            
            reseller_pix_before = reseller_config_before.get("pix_key", "")
            reseller_ai_name_before = reseller_config_before.get("ai_agent", {}).get("name", "")
            print(f"      - Reseller PIX key BEFORE: '{reseller_pix_before}'")
            print(f"      - Reseller AI agent name BEFORE: '{reseller_ai_name_before}'")
            
            # Step 3: Execute replication
            print("   🚀 Step 3: Executing replication...")
            success, replication_response = self.make_request("POST", "/admin/replicate-config-to-resellers", token=self.admin_token)
            
            if not success or not replication_response.get("ok"):
                self.log_result("Replication Functionality", False, f"Replication failed: {replication_response}")
                return False
            
            total_resellers = replication_response.get("total_resellers", 0)
            replicated_count = replication_response.get("replicated_count", 0)
            message = replication_response.get("message", "")
            
            print(f"      ✅ Replication completed: {message}")
            print(f"      - Total resellers: {total_resellers}")
            print(f"      - Successfully replicated: {replicated_count}")
            
            # Step 4: Verify response structure
            print("   📋 Step 4: Verifying response structure...")
            required_fields = ["ok", "message", "total_resellers", "replicated_count"]
            missing_fields = [field for field in required_fields if field not in replication_response]
            
            if missing_fields:
                self.log_result("Replication Functionality", False, f"Missing response fields: {missing_fields}")
                return False
            
            print(f"      ✅ Response structure correct: {required_fields}")
            
            # Step 5: Get reseller config AFTER replication
            print("   🔍 Step 5: Getting reseller config AFTER replication...")
            success, reseller_config_after = self.make_request("GET", "/config", token=self.reseller_token)
            if not success:
                self.log_result("Replication Functionality", False, f"Failed to get reseller config after replication: {reseller_config_after}")
                return False
            
            reseller_pix_after = reseller_config_after.get("pix_key", "")
            reseller_ai_name_after = reseller_config_after.get("ai_agent", {}).get("name", "")
            print(f"      - Reseller PIX key AFTER: '{reseller_pix_after}'")
            print(f"      - Reseller AI agent name AFTER: '{reseller_ai_name_after}'")
            
            # Step 6: Verify configurations were copied
            print("   ✅ Step 6: Verifying configurations were copied...")
            
            configs_copied = True
            copy_details = []
            
            # Check PIX key
            if admin_pix_before == reseller_pix_after:
                copy_details.append(f"PIX key copied: '{admin_pix_before}'")
            else:
                copy_details.append(f"PIX key NOT copied: admin='{admin_pix_before}' vs reseller='{reseller_pix_after}'")
                configs_copied = False
            
            # Check AI agent name
            if admin_ai_name_before == reseller_ai_name_after:
                copy_details.append(f"AI agent name copied: '{admin_ai_name_before}'")
            else:
                copy_details.append(f"AI agent name NOT copied: admin='{admin_ai_name_before}' vs reseller='{reseller_ai_name_after}'")
                configs_copied = False
            
            # Check other important fields
            admin_allowed_data = admin_config_before.get("allowed_data", {})
            reseller_allowed_data = reseller_config_after.get("allowed_data", {})
            
            if admin_allowed_data == reseller_allowed_data:
                copy_details.append("Allowed data copied correctly")
            else:
                copy_details.append("Allowed data NOT copied correctly")
                configs_copied = False
            
            admin_api_integration = admin_config_before.get("api_integration", {})
            reseller_api_integration = reseller_config_after.get("api_integration", {})
            
            if admin_api_integration == reseller_api_integration:
                copy_details.append("API integration copied correctly")
            else:
                copy_details.append("API integration NOT copied correctly")
                configs_copied = False
            
            # Print verification details
            for detail in copy_details:
                print(f"      - {detail}")
            
            # Step 7: Validate replication count
            print("   📊 Step 7: Validating replication count...")
            
            if replicated_count > total_resellers:
                self.log_result("Replication Functionality", False, f"Replicated count ({replicated_count}) > total resellers ({total_resellers})")
                return False
            
            if total_resellers > 0 and replicated_count == 0:
                self.log_result("Replication Functionality", False, f"No resellers were replicated despite {total_resellers} existing")
                return False
            
            print(f"      ✅ Replication count valid: {replicated_count}/{total_resellers}")
            
            # Final result
            if configs_copied and replicated_count > 0:
                self.log_result("Replication Functionality", True, f"Configurations successfully copied to {replicated_count} resellers")
                return True
            else:
                self.log_result("Replication Functionality", False, f"Configuration copying failed or no resellers updated")
                return False
                
        except Exception as e:
            self.log_result("Replication Functionality", False, f"Exception during functionality test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all replication endpoint tests"""
        print("🚀 TESTE ESPECÍFICO DO ENDPOINT DE REPLICAÇÃO DE CONFIGURAÇÕES")
        print("=" * 70)
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📋 Endpoint: POST /api/admin/replicate-config-to-resellers")
        print("=" * 70)
        
        tests = [
            self.test_admin_login,
            self.test_reseller_login,
            self.test_admin_replication_auth,
            self.test_reseller_replication_auth,
            self.test_replication_functionality,
        ]
        
        passed = 0
        total = len(tests)
        failed_tests = []
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed_tests.append(test.__name__)
                print()  # Add spacing between tests
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                failed_tests.append(test.__name__)
                print()
                
        print("=" * 70)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Endpoint de replicação funcionando corretamente.")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
        
        print("=" * 70)
        return passed, total

if __name__ == "__main__":
    tester = ReplicationEndpointTester()
    tester.run_all_tests()