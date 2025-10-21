#!/usr/bin/env python3
"""
TESTE COMPLETO DO BACKEND - APÓS CORREÇÕES CRÍTICAS
Testa todas as rotas críticas: autenticação, atendentes, agentes IA, departamentos, config, revendas
"""

import requests
import json
import os
from typing import Dict, Optional, List
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supportdesk-pro.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"  # From .env file

class ComprehensiveBackendTester:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.client_token = None
        self.reseller_token = None
        self.created_agents = []
        self.created_ai_agents = []
        self.created_departments = []
        self.created_resellers = []
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
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
            
    # ============================================
    # TESTES DE AUTENTICAÇÃO
    # ============================================
    
    def test_admin_login(self) -> bool:
        """Test 1: POST /api/auth/admin/login (senha: 102030@ab)"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Token received: {response['user_type']}")
            return True
        else:
            self.log_result("Admin Login", False, f"Error: {response}")
            return False
    
    def test_agent_login(self) -> bool:
        """Test 2: POST /api/auth/agent/login"""
        # First create an agent
        if not self.admin_token:
            self.log_result("Agent Login", False, "Admin token required")
            return False
            
        agent_data = {
            "name": "Agente Teste",
            "login": "agente_teste",
            "password": "123456",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        if not success:
            self.log_result("Agent Login", False, f"Failed to create agent: {response}")
            return False
            
        agent_id = response.get("id")
        if agent_id:
            self.created_agents.append(agent_id)
        
        # Now test login
        login_data = {
            "login": "agente_teste",
            "password": "123456"
        }
        
        success, response = self.make_request("POST", "/auth/agent/login", login_data)
        
        if success and "token" in response:
            self.agent_token = response["token"]
            self.log_result("Agent Login", True, f"Agent logged in: {response.get('user_data', {}).get('name')}")
            return True
        else:
            self.log_result("Agent Login", False, f"Error: {response}")
            return False
    
    def test_client_login(self) -> bool:
        """Test 3: POST /api/auth/client/login"""
        login_data = {
            "whatsapp": "11999999999",
            "pin": "12"
        }
        
        success, response = self.make_request("POST", "/auth/client/login", login_data)
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.log_result("Client Login", True, f"Client logged in: {response.get('user_data', {}).get('whatsapp')}")
            return True
        else:
            self.log_result("Client Login", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE ATENDENTES
    # ============================================
    
    def test_list_agents(self) -> bool:
        """Test 4: GET /api/agents (listar atendentes)"""
        if not self.admin_token:
            self.log_result("List Agents", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/agents", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Agents", True, f"Found {count} agents")
            return True
        else:
            self.log_result("List Agents", False, f"Error: {response}")
            return False
    
    def test_create_agent(self) -> bool:
        """Test 5: POST /api/agents (criar atendente)"""
        if not self.admin_token:
            self.log_result("Create Agent", False, "Admin token required")
            return False
            
        agent_data = {
            "name": "Novo Agente Teste",
            "login": "novo_agente",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        
        if success and response.get("ok"):
            agent_id = response.get("id")
            if agent_id:
                self.created_agents.append(agent_id)
            self.log_result("Create Agent", True, f"Agent created with ID: {agent_id}")
            return True
        else:
            self.log_result("Create Agent", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE AGENTES IA (PRIORIDADE ALTA)
    # ============================================
    
    def test_list_ai_agents(self) -> bool:
        """Test 6: GET /api/ai/agents (listar agentes IA)"""
        if not self.admin_token:
            self.log_result("List AI Agents", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/ai/agents", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List AI Agents", True, f"Found {count} AI agents")
            return True
        else:
            self.log_result("List AI Agents", False, f"Error: {response}")
            return False
    
    def test_create_ai_agent(self) -> bool:
        """Test 7: POST /api/ai/agents (criar agente IA)"""
        if not self.admin_token:
            self.log_result("Create AI Agent", False, "Admin token required")
            return False
            
        ai_agent_data = {
            "name": "Agente IA Teste",
            "description": "Agente de teste para validação",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        }
        
        success, response = self.make_request("POST", "/ai/agents", ai_agent_data, self.admin_token)
        
        if success and "id" in response:
            agent_id = response.get("id")
            self.created_ai_agents.append(agent_id)
            self.log_result("Create AI Agent", True, f"AI Agent created: {response.get('name')} (ID: {agent_id})")
            return True
        else:
            self.log_result("Create AI Agent", False, f"Error: {response}")
            return False
    
    def test_update_ai_agent(self) -> bool:
        """Test 8: PUT /api/ai/agents/{id} (atualizar agente)"""
        if not self.admin_token or not self.created_ai_agents:
            self.log_result("Update AI Agent", False, "Admin token or AI agent required")
            return False
            
        agent_id = self.created_ai_agents[0]
        update_data = {
            "name": "Agente IA Atualizado",
            "description": "Descrição atualizada",
            "temperature": 0.8
        }
        
        success, response = self.make_request("PUT", f"/ai/agents/{agent_id}", update_data, self.admin_token)
        
        if success and "id" in response:
            self.log_result("Update AI Agent", True, f"AI Agent updated: {response.get('name')}")
            return True
        else:
            self.log_result("Update AI Agent", False, f"Error: {response}")
            return False
    
    def test_delete_ai_agent(self) -> bool:
        """Test 9: DELETE /api/ai/agents/{id} (deletar agente)"""
        if not self.admin_token or not self.created_ai_agents:
            self.log_result("Delete AI Agent", False, "Admin token or AI agent required")
            return False
            
        agent_id = self.created_ai_agents[-1]  # Delete the last one
        
        success, response = self.make_request("DELETE", f"/ai/agents/{agent_id}", token=self.admin_token)
        
        if success and response.get("ok"):
            self.created_ai_agents.remove(agent_id)
            self.log_result("Delete AI Agent", True, f"AI Agent deleted: {agent_id}")
            return True
        else:
            self.log_result("Delete AI Agent", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE DEPARTAMENTOS (PRIORIDADE ALTA)
    # ============================================
    
    def test_list_departments(self) -> bool:
        """Test 10: GET /api/ai/departments (listar departamentos)"""
        if not self.admin_token:
            self.log_result("List Departments", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/ai/departments", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Departments", True, f"Found {count} departments")
            return True
        else:
            self.log_result("List Departments", False, f"Error: {response}")
            return False
    
    def test_create_department(self) -> bool:
        """Test 11: POST /api/ai/departments (criar departamento)"""
        if not self.admin_token:
            self.log_result("Create Department", False, "Admin token required")
            return False
            
        dept_data = {
            "name": "Suporte Técnico",
            "description": "Departamento de suporte técnico",
            "is_default": True,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", dept_data, self.admin_token)
        
        if success and "id" in response:
            dept_id = response.get("id")
            self.created_departments.append(dept_id)
            self.log_result("Create Department", True, f"Department created: {response.get('name')} (ID: {dept_id})")
            return True
        else:
            self.log_result("Create Department", False, f"Error: {response}")
            return False
    
    def test_update_department(self) -> bool:
        """Test 12: PUT /api/ai/departments/{id} (atualizar)"""
        if not self.admin_token or not self.created_departments:
            self.log_result("Update Department", False, "Admin token or department required")
            return False
            
        dept_id = self.created_departments[0]
        update_data = {
            "name": "Suporte Técnico Atualizado",
            "description": "Descrição atualizada do departamento",
            "timeout_seconds": 180
        }
        
        success, response = self.make_request("PUT", f"/ai/departments/{dept_id}", update_data, self.admin_token)
        
        if success and "id" in response:
            self.log_result("Update Department", True, f"Department updated: {response.get('name')}")
            return True
        else:
            self.log_result("Update Department", False, f"Error: {response}")
            return False
    
    def test_delete_department(self) -> bool:
        """Test 13: DELETE /api/ai/departments/{id} (deletar)"""
        if not self.admin_token or not self.created_departments:
            self.log_result("Delete Department", False, "Admin token or department required")
            return False
            
        dept_id = self.created_departments[-1]  # Delete the last one
        
        success, response = self.make_request("DELETE", f"/ai/departments/{dept_id}", token=self.admin_token)
        
        if success and response.get("ok"):
            self.created_departments.remove(dept_id)
            self.log_result("Delete Department", True, f"Department deleted: {dept_id}")
            return True
        else:
            self.log_result("Delete Department", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE CONFIG
    # ============================================
    
    def test_get_config(self) -> bool:
        """Test 14: GET /api/config (obter configurações)"""
        if not self.admin_token:
            self.log_result("Get Config", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/config", token=self.admin_token)
        
        if success and isinstance(response, dict):
            # Check for required fields
            required_fields = ["quick_blocks", "auto_reply", "apps", "pix_key", "allowed_data", "api_integration", "ai_agent"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_result("Get Config", True, f"Config loaded with all required fields")
                return True
            else:
                self.log_result("Get Config", False, f"Missing fields: {missing_fields}")
                return False
        else:
            self.log_result("Get Config", False, f"Error: {response}")
            return False
    
    def test_update_config(self) -> bool:
        """Test 15: PUT /api/config (atualizar configurações)"""
        if not self.admin_token:
            self.log_result("Update Config", False, "Admin token required")
            return False
            
        config_data = {
            "quick_blocks": [{"name": "Teste", "text": "Mensagem de teste"}],
            "auto_reply": [{"q": "oi", "a": "Olá! Como posso ajudar?"}],
            "apps": [],
            "pix_key": "test-pix-key-123",
            "allowed_data": {
                "cpfs": ["123.456.789-00"],
                "emails": ["test@example.com"],
                "phones": ["11999999999"],
                "random_keys": ["test-key-123"]
            },
            "api_integration": {
                "api_url": "https://api.test.com",
                "api_token": "test-token",
                "api_enabled": True
            },
            "ai_agent": {
                "name": "Assistente IA Teste",
                "personality": "Amigável e prestativo",
                "instructions": "Sempre seja educado",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
                "mode": "standby",
                "active_hours": "24/7",
                "enabled": True,
                "can_access_credentials": True,
                "knowledge_base": "Base de conhecimento teste"
            }
        }
        
        success, response = self.make_request("PUT", "/config", config_data, self.admin_token)
        
        if success and response.get("ok"):
            self.log_result("Update Config", True, "Config updated successfully")
            return True
        else:
            self.log_result("Update Config", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES DE REVENDAS
    # ============================================
    
    def test_list_resellers(self) -> bool:
        """Test 16: GET /api/resellers (listar)"""
        if not self.admin_token:
            self.log_result("List Resellers", False, "Admin token required")
            return False
            
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            count = len(response)
            self.log_result("List Resellers", True, f"Found {count} resellers")
            return True
        else:
            self.log_result("List Resellers", False, f"Error: {response}")
            return False
    
    def test_create_reseller(self) -> bool:
        """Test 17: POST /api/resellers (criar)"""
        if not self.admin_token:
            self.log_result("Create Reseller", False, "Admin token required")
            return False
            
        reseller_data = {
            "name": "Revenda Teste Backend",
            "email": "teste@backend.com",
            "password": "senha123",
            "domain": "teste.backend.com",
            "parent_id": None
        }
        
        success, response = self.make_request("POST", "/resellers", reseller_data, self.admin_token)
        
        if success and response.get("ok"):
            reseller_id = response.get("reseller_id")
            if reseller_id:
                self.created_resellers.append(reseller_id)
            self.log_result("Create Reseller", True, f"Reseller created with ID: {reseller_id}")
            return True
        else:
            self.log_result("Create Reseller", False, f"Error: {response}")
            return False
    
    def test_reseller_login(self) -> bool:
        """Test 18: Reseller Login (michaelrv@gmail.com / ab181818ab)"""
        login_data = {
            "email": "michaelrv@gmail.com",
            "password": "ab181818ab"
        }
        
        success, response = self.make_request("POST", "/resellers/login", login_data)
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            reseller_id = response.get("reseller_id")
            self.log_result("Reseller Login (ajuda.vip)", True, f"Reseller logged in: {reseller_id}")
            return True
        else:
            self.log_result("Reseller Login (ajuda.vip)", False, f"Error: {response}")
            return False
            
    # ============================================
    # TESTES ESPECIAIS - VERIFICAÇÃO DE BANCO CORRETO
    # ============================================
    
    def test_database_consistency(self) -> bool:
        """Test 19: Verificar se rotas de IA acessam banco correto (support_chat)"""
        if not self.admin_token:
            self.log_result("Database Consistency", False, "Admin token required")
            return False
        
        # Test AI agents endpoint
        success_ai, response_ai = self.make_request("GET", "/ai/agents", token=self.admin_token)
        
        # Test departments endpoint  
        success_dept, response_dept = self.make_request("GET", "/ai/departments", token=self.admin_token)
        
        # Test regular agents endpoint
        success_agents, response_agents = self.make_request("GET", "/agents", token=self.admin_token)
        
        if success_ai and success_dept and success_agents:
            self.log_result("Database Consistency", True, "All endpoints accessible - using correct database")
            return True
        else:
            errors = []
            if not success_ai:
                errors.append(f"AI agents: {response_ai}")
            if not success_dept:
                errors.append(f"Departments: {response_dept}")
            if not success_agents:
                errors.append(f"Agents: {response_agents}")
            self.log_result("Database Consistency", False, f"Errors: {'; '.join(errors)}")
            return False
            
    # ============================================
    # TESTES DE WHATSAPP E PIN (FASE 4)
    # ============================================
    
    def test_whatsapp_popup_status(self) -> bool:
        """Test 20: GET /users/whatsapp-popup-status"""
        if not self.client_token:
            self.log_result("WhatsApp Popup Status", False, "Client token required")
            return False
            
        success, response = self.make_request("GET", "/users/whatsapp-popup-status", token=self.client_token)
        
        if success and "should_show" in response:
            should_show = response.get("should_show")
            self.log_result("WhatsApp Popup Status", True, f"Should show popup: {should_show}")
            return True
        else:
            self.log_result("WhatsApp Popup Status", False, f"Error: {response}")
            return False
    
    def test_whatsapp_confirm(self) -> bool:
        """Test 21: PUT /users/me/whatsapp-confirm"""
        if not self.client_token:
            self.log_result("WhatsApp Confirm", False, "Client token required")
            return False
            
        confirm_data = {
            "whatsapp": "11999999999"
        }
        
        success, response = self.make_request("PUT", "/users/me/whatsapp-confirm", confirm_data, self.client_token)
        
        if success and response.get("ok"):
            self.log_result("WhatsApp Confirm", True, "WhatsApp confirmed successfully")
            return True
        else:
            self.log_result("WhatsApp Confirm", False, f"Error: {response}")
            return False
    
    def test_update_pin(self) -> bool:
        """Test 22: PUT /users/me/pin"""
        if not self.client_token:
            self.log_result("Update PIN", False, "Client token required")
            return False
            
        pin_data = {
            "pin": "34"
        }
        
        success, response = self.make_request("PUT", "/users/me/pin", pin_data, self.client_token)
        
        if success and response.get("ok"):
            self.log_result("Update PIN", True, "PIN updated successfully")
            return True
        else:
            self.log_result("Update PIN", False, f"Error: {response}")
            return False
    
    def test_invalid_pin(self) -> bool:
        """Test 23: PUT /users/me/pin (validação de PIN inválido)"""
        if not self.client_token:
            self.log_result("Invalid PIN Validation", False, "Client token required")
            return False
            
        pin_data = {
            "pin": "123"  # Invalid - should be 2 digits
        }
        
        success, response = self.make_request("PUT", "/users/me/pin", pin_data, self.client_token)
        
        # Should fail with validation error
        if not success and "2 dígitos" in str(response):
            self.log_result("Invalid PIN Validation", True, "Correctly rejected invalid PIN")
            return True
        else:
            self.log_result("Invalid PIN Validation", False, f"Should have rejected invalid PIN: {response}")
            return False
            
    # ============================================
    # CLEANUP METHODS
    # ============================================
            
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        if not self.admin_token:
            print("❌ No admin token for cleanup")
            return
        
        # Delete created AI agents
        for agent_id in self.created_ai_agents:
            success, response = self.make_request("DELETE", f"/ai/agents/{agent_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted AI agent: {agent_id}")
            else:
                print(f"❌ Failed to delete AI agent {agent_id}: {response}")
        
        # Delete created departments
        for dept_id in self.created_departments:
            success, response = self.make_request("DELETE", f"/ai/departments/{dept_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted department: {dept_id}")
            else:
                print(f"❌ Failed to delete department {dept_id}: {response}")
        
        # Delete created agents
        for agent_id in self.created_agents:
            success, response = self.make_request("DELETE", f"/agents/{agent_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted agent: {agent_id}")
            else:
                print(f"❌ Failed to delete agent {agent_id}: {response}")
        
        # Delete created resellers (in reverse order to handle hierarchy)
        for reseller_id in reversed(self.created_resellers):
            success, response = self.make_request("DELETE", f"/resellers/{reseller_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted reseller: {reseller_id}")
            else:
                print(f"❌ Failed to delete reseller {reseller_id}: {response}")
                
    def run_all_tests(self):
        """Run all critical backend tests"""
        print("🚀 TESTE COMPLETO DO BACKEND - APÓS CORREÇÕES CRÍTICAS")
        print("=" * 60)
        
        tests = [
            # Authentication Tests
            self.test_admin_login,
            self.test_agent_login,
            self.test_client_login,
            
            # Agents Tests
            self.test_list_agents,
            self.test_create_agent,
            
            # AI Agents Tests (HIGH PRIORITY)
            self.test_list_ai_agents,
            self.test_create_ai_agent,
            self.test_update_ai_agent,
            self.test_delete_ai_agent,
            
            # Departments Tests (HIGH PRIORITY)
            self.test_list_departments,
            self.test_create_department,
            self.test_update_department,
            self.test_delete_department,
            
            # Config Tests
            self.test_get_config,
            self.test_update_config,
            
            # Resellers Tests
            self.test_list_resellers,
            self.test_create_reseller,
            self.test_reseller_login,
            
            # Special Tests
            self.test_database_consistency,
            
            # WhatsApp & PIN Tests (Phase 4)
            self.test_whatsapp_popup_status,
            self.test_whatsapp_confirm,
            self.test_update_pin,
            self.test_invalid_pin
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
                time.sleep(0.3)  # Small delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                failed_tests.append(test.__name__)
                
        print("\n" + "=" * 60)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Backend funcionando corretamente.")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            
        # Cleanup
        if any([self.created_agents, self.created_ai_agents, self.created_departments, self.created_resellers]):
            self.cleanup()
            
        return passed, total, self.test_results

def main():
    """Main test execution"""
    print(f"🔗 Testing backend at: {API_BASE}")
    print(f"🎯 Focusing on critical routes after fixes")
    
    tester = ComprehensiveBackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Return results for external processing
    return {
        "passed": passed,
        "total": total,
        "success_rate": (passed / total) * 100 if total > 0 else 0,
        "results": results
    }

if __name__ == "__main__":
    main()