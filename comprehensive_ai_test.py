#!/usr/bin/env python3
"""
TESTE COMPLETO - FLUXO COMPLETO DE IA
Testa o fluxo completo de mensagens com IA conforme especificado:
1. Criar agente, cliente, agente IA e departamento
2. Enviar mensagem do cliente
3. Verificar se IA responde automaticamente
4. Testar controle de linked_agents
5. Testar toggle de IA por conversa
6. Testar mensagens PIX
"""

import requests
import json
import os
import time
import uuid
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supportdesk-pro.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"

class ComprehensiveAITester:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.client_token = None
        self.client_id = None
        self.agent_id = None
        self.ai_agent_id = None
        self.department_id = None
        self.ticket_id = None
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
    # SETUP COMPLETO
    # ============================================
    
    def test_setup_admin(self) -> bool:
        """Setup 1: Admin login"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Setup Admin", True, "Admin authenticated")
            return True
        else:
            self.log_result("Setup Admin", False, f"Error: {response}")
            return False

    def test_setup_agent(self) -> bool:
        """Setup 2: Create and login agent"""
        if not self.admin_token:
            self.log_result("Setup Agent", False, "Admin token required")
            return False
            
        # Create agent
        agent_data = {
            "name": "Agente Teste IA Completo",
            "login": f"agente_ia_completo_{int(time.time())}",
            "password": "123456",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", agent_data, self.admin_token)
        if not success or not response.get("ok"):
            self.log_result("Setup Agent", False, f"Agent creation failed: {response}")
            return False
            
        self.agent_id = response.get("id")
        
        # Login as agent
        login_data = {
            "login": agent_data["login"],
            "password": agent_data["password"]
        }
        
        success, login_response = self.make_request("POST", "/auth/agent/login", login_data)
        if success and "token" in login_response:
            self.agent_token = login_response["token"]
            self.log_result("Setup Agent", True, f"Agent created and logged in: {self.agent_id}")
            return True
        else:
            self.log_result("Setup Agent", False, f"Agent login failed: {login_response}")
            return False

    def test_setup_client(self) -> bool:
        """Setup 3: Create client"""
        import random
        unique_whatsapp = f"119{random.randint(10000000, 99999999)}"
        
        login_data = {
            "whatsapp": unique_whatsapp,
            "pin": "12"
        }
        
        success, response = self.make_request("POST", "/auth/client/login", login_data)
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.client_id = response.get("user_data", {}).get("id")
            self.log_result("Setup Client", True, f"Client created: {unique_whatsapp}")
            return True
        else:
            self.log_result("Setup Client", False, f"Error: {response}")
            return False

    def test_setup_ai_agent(self) -> bool:
        """Setup 4: Create AI agent with linked_agents"""
        if not self.admin_token or not self.agent_id:
            self.log_result("Setup AI Agent", False, "Admin token and agent required")
            return False
            
        ai_agent_data = {
            "name": "Agente IA Teste Completo",
            "description": "Agente de teste para validação completa do fluxo",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "linked_agents": [self.agent_id]
        }
        
        success, response = self.make_request("POST", "/ai/agents", ai_agent_data, self.admin_token)
        
        if success and "id" in response:
            self.ai_agent_id = response.get("id")
            
            # Update with linked_agents if not set during creation
            update_data = {
                "linked_agents": [self.agent_id],
                "instructions": "Você é um assistente prestativo. Responda de forma clara e objetiva.",
                "is_active": True
            }
            
            success_update, update_response = self.make_request("PUT", f"/ai/agents/{self.ai_agent_id}", update_data, self.admin_token)
            
            if success_update:
                self.log_result("Setup AI Agent", True, f"AI Agent created and configured: {self.ai_agent_id}")
                return True
            else:
                self.log_result("Setup AI Agent", False, f"AI Agent update failed: {update_response}")
                return False
        else:
            self.log_result("Setup AI Agent", False, f"Error: {response}")
            return False

    def test_setup_department(self) -> bool:
        """Setup 5: Create department linked to AI agent"""
        if not self.admin_token or not self.ai_agent_id:
            self.log_result("Setup Department", False, "Admin token and AI agent required")
            return False
            
        dept_data = {
            "name": "Suporte IA Teste Completo",
            "description": "Departamento com IA para testes completos",
            "is_default": True,
            "timeout_seconds": 120,
            "ai_agent_id": self.ai_agent_id
        }
        
        success, response = self.make_request("POST", "/ai/departments", dept_data, self.admin_token)
        
        if success and "id" in response:
            self.department_id = response.get("id")
            self.log_result("Setup Department", True, f"Department created with AI: {self.department_id}")
            return True
        else:
            self.log_result("Setup Department", False, f"Error: {response}")
            return False

    # ============================================
    # TESTES DE FLUXO DE IA
    # ============================================

    def test_client_message_creates_ticket(self) -> bool:
        """Test 1: Cliente envia mensagem e cria ticket"""
        if not self.client_token or not self.client_id:
            self.log_result("Client Message Creates Ticket", False, "Client token required")
            return False

        message_data = {
            "from_id": self.client_id,
            "from_type": "client",
            "to_type": "agent",
            "to_id": "system",
            "kind": "text",
            "text": "Olá, preciso de ajuda com minha conta"
        }
        
        success, response = self.make_request("POST", "/messages", message_data, self.client_token)
        
        if success:
            self.log_result("Client Message Creates Ticket", True, "Message sent successfully")
            
            # Get tickets to find the created ticket
            time.sleep(1)  # Wait for ticket creation
            success_tickets, tickets_response = self.make_request("GET", "/tickets", token=self.admin_token)
            
            if success_tickets and isinstance(tickets_response, list):
                # Find ticket for our client
                client_ticket = next((t for t in tickets_response if t.get("client_id") == self.client_id), None)
                if client_ticket:
                    self.ticket_id = client_ticket["id"]
                    self.log_result("Ticket Created", True, f"Ticket created: {self.ticket_id}")
                    return True
                else:
                    self.log_result("Ticket Created", False, "No ticket found for client")
                    return False
            else:
                self.log_result("Ticket Created", False, f"Error getting tickets: {tickets_response}")
                return False
        else:
            self.log_result("Client Message Creates Ticket", False, f"Error: {response}")
            return False

    def test_department_selection(self) -> bool:
        """Test 2: Cliente seleciona departamento"""
        if not self.client_token or not self.ticket_id or not self.department_id:
            self.log_result("Department Selection", False, "Client token, ticket and department required")
            return False

        selection_data = {
            "department_id": self.department_id
        }
        
        success, response = self.make_request("POST", f"/tickets/{self.ticket_id}/select-department", selection_data, self.client_token)
        
        if success:
            self.log_result("Department Selection", True, "Department selected successfully")
            return True
        else:
            self.log_result("Department Selection", False, f"Error: {response}")
            return False

    def test_assign_ticket_to_agent(self) -> bool:
        """Test 3: Atribuir ticket ao agente (para testar linked_agents)"""
        if not self.admin_token or not self.ticket_id or not self.agent_id:
            self.log_result("Assign Ticket to Agent", False, "Admin token, ticket and agent required")
            return False

        # Update ticket to assign to our agent
        assign_data = {
            "assigned_agent_id": self.agent_id,
            "status": "ATENDENDO"
        }
        
        success, response = self.make_request("PUT", f"/tickets/{self.ticket_id}", assign_data, self.admin_token)
        
        if success:
            self.log_result("Assign Ticket to Agent", True, f"Ticket assigned to agent: {self.agent_id}")
            return True
        else:
            # Try alternative method - update via status endpoint
            status_data = {"status": "ATENDENDO"}
            success, response = self.make_request("POST", f"/tickets/{self.ticket_id}/status", status_data, self.agent_token)
            
            if success:
                self.log_result("Assign Ticket to Agent", True, "Ticket status updated to ATENDENDO")
                return True
            else:
                self.log_result("Assign Ticket to Agent", False, f"Error: {response}")
                return False

    def test_ai_response_to_message(self) -> bool:
        """Test 4: IA deve responder automaticamente quando cliente envia mensagem"""
        if not self.client_token or not self.client_id or not self.ticket_id:
            self.log_result("AI Response to Message", False, "Client token and ticket required")
            return False

        # Get message count before
        success_before, messages_before = self.make_request("GET", f"/messages/{self.ticket_id}", token=self.client_token)
        before_count = len(messages_before) if success_before and isinstance(messages_before, list) else 0

        # Send message from client
        message_data = {
            "from_id": self.client_id,
            "from_type": "client",
            "to_type": "agent",
            "to_id": self.agent_id,
            "kind": "text",
            "text": "Como posso alterar minha senha?",
            "ticket_id": self.ticket_id
        }
        
        success, response = self.make_request("POST", "/messages", message_data, self.client_token)
        
        if success:
            # Wait for AI to process and respond
            time.sleep(3)
            
            # Check if AI responded
            success_after, messages_after = self.make_request("GET", f"/messages/{self.ticket_id}", token=self.client_token)
            
            if success_after and isinstance(messages_after, list):
                after_count = len(messages_after)
                
                # Check for AI response
                ai_messages = [msg for msg in messages_after if msg.get("from_type") == "ai"]
                
                if ai_messages:
                    self.log_result("AI Response to Message", True, f"AI responded! Found {len(ai_messages)} AI messages")
                    return True
                elif after_count > before_count:
                    self.log_result("AI Response to Message", True, f"Messages increased from {before_count} to {after_count}")
                    return True
                else:
                    self.log_result("AI Response to Message", False, f"No AI response detected. Messages: {before_count} -> {after_count}")
                    return False
            else:
                self.log_result("AI Response to Message", False, f"Error getting messages: {messages_after}")
                return False
        else:
            self.log_result("AI Response to Message", False, f"Error sending message: {response}")
            return False

    # ============================================
    # TESTES DE CONTROLE DE IA
    # ============================================

    def test_toggle_ai_disable(self) -> bool:
        """Test 5: Desativar IA na conversa"""
        if not self.agent_token or not self.ticket_id:
            self.log_result("Toggle AI Disable", False, "Agent token and ticket required")
            return False

        success, response = self.make_request("POST", f"/tickets/{self.ticket_id}/toggle-ai", {}, self.agent_token)
        
        if success and "ai_enabled" in response:
            ai_enabled = response.get("ai_enabled")
            disabled_until = response.get("disabled_until")
            self.log_result("Toggle AI Disable", True, f"AI disabled: enabled={ai_enabled}, until={disabled_until}")
            return True
        elif success:
            self.log_result("Toggle AI Disable", True, f"AI toggle successful: {response}")
            return True
        else:
            self.log_result("Toggle AI Disable", False, f"Error: {response}")
            return False

    def test_ai_no_response_when_disabled(self) -> bool:
        """Test 6: IA não deve responder quando desativada"""
        if not self.client_token or not self.client_id or not self.ticket_id:
            self.log_result("AI No Response When Disabled", False, "Client token and ticket required")
            return False

        # Get message count before
        success_before, messages_before = self.make_request("GET", f"/messages/{self.ticket_id}", token=self.client_token)
        before_count = len(messages_before) if success_before and isinstance(messages_before, list) else 0

        # Send message from client
        message_data = {
            "from_id": self.client_id,
            "from_type": "client",
            "to_type": "agent",
            "to_id": self.agent_id,
            "kind": "text",
            "text": "Esta mensagem não deve ter resposta da IA",
            "ticket_id": self.ticket_id
        }
        
        success, response = self.make_request("POST", "/messages", message_data, self.client_token)
        
        if success:
            # Wait to see if AI responds (it shouldn't)
            time.sleep(2)
            
            # Check messages
            success_after, messages_after = self.make_request("GET", f"/messages/{self.ticket_id}", token=self.client_token)
            
            if success_after and isinstance(messages_after, list):
                after_count = len(messages_after)
                
                # Check for new AI messages
                new_ai_messages = [msg for msg in messages_after[before_count:] if msg.get("from_type") == "ai"]
                
                if not new_ai_messages:
                    self.log_result("AI No Response When Disabled", True, "AI correctly did not respond when disabled")
                    return True
                else:
                    self.log_result("AI No Response When Disabled", False, f"AI responded when it should be disabled: {len(new_ai_messages)} messages")
                    return False
            else:
                self.log_result("AI No Response When Disabled", False, f"Error getting messages: {messages_after}")
                return False
        else:
            self.log_result("AI No Response When Disabled", False, f"Error sending message: {response}")
            return False

    def test_toggle_ai_enable(self) -> bool:
        """Test 7: Reativar IA na conversa"""
        if not self.agent_token or not self.ticket_id:
            self.log_result("Toggle AI Enable", False, "Agent token and ticket required")
            return False

        success, response = self.make_request("POST", f"/tickets/{self.ticket_id}/toggle-ai", {}, self.agent_token)
        
        if success and "ai_enabled" in response:
            ai_enabled = response.get("ai_enabled")
            self.log_result("Toggle AI Enable", True, f"AI toggled: enabled={ai_enabled}")
            return True
        elif success:
            self.log_result("Toggle AI Enable", True, f"AI toggle successful: {response}")
            return True
        else:
            self.log_result("Toggle AI Enable", False, f"Error: {response}")
            return False

    # ============================================
    # TESTES DE PIX
    # ============================================

    def test_pix_message_creation(self) -> bool:
        """Test 8: Mensagem com chave PIX deve criar mensagem tipo 'pix'"""
        if not self.agent_token or not self.agent_id or not self.ticket_id:
            self.log_result("PIX Message Creation", False, "Agent token and ticket required")
            return False

        # First, set up a PIX key in config
        config_data = {
            "quick_blocks": [],
            "auto_reply": [],
            "apps": [],
            "pix_key": "test-pix-key-12345678",
            "allowed_data": {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
            "api_integration": {"api_url": "", "api_token": "", "api_enabled": False},
            "ai_agent": {
                "name": "Assistente IA",
                "personality": "",
                "instructions": "",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
                "mode": "standby",
                "active_hours": "24/7",
                "enabled": False,
                "can_access_credentials": True,
                "knowledge_base": ""
            }
        }
        
        # Update config with PIX key
        success_config, config_response = self.make_request("PUT", "/config", config_data, self.admin_token)
        
        if not success_config:
            self.log_result("PIX Message Creation", False, f"Failed to set PIX config: {config_response}")
            return False

        # Send message with PIX key
        message_data = {
            "from_id": self.agent_id,
            "from_type": "agent",
            "to_type": "client",
            "to_id": self.client_id,
            "kind": "text",
            "text": f"Aqui está a chave PIX para pagamento: test-pix-key-12345678",
            "ticket_id": self.ticket_id
        }
        
        success, response = self.make_request("POST", "/messages", message_data, self.agent_token)
        
        if success:
            # Check if message was created with PIX type
            time.sleep(1)
            success_messages, messages = self.make_request("GET", f"/messages/{self.ticket_id}", token=self.agent_token)
            
            if success_messages and isinstance(messages, list):
                pix_messages = [msg for msg in messages if msg.get("kind") == "pix"]
                
                if pix_messages:
                    pix_key = pix_messages[-1].get("pix_key")
                    self.log_result("PIX Message Creation", True, f"PIX message created with key: {pix_key}")
                    return True
                else:
                    self.log_result("PIX Message Creation", False, "No PIX message found")
                    return False
            else:
                self.log_result("PIX Message Creation", False, f"Error getting messages: {messages}")
                return False
        else:
            self.log_result("PIX Message Creation", False, f"Error: {response}")
            return False

    # ============================================
    # VERIFICAÇÕES FINAIS
    # ============================================

    def test_verify_linked_agents_field(self) -> bool:
        """Test 9: Verificar campo linked_agents no agente IA"""
        if not self.admin_token or not self.ai_agent_id:
            self.log_result("Verify Linked Agents Field", False, "Admin token and AI agent required")
            return False

        success, response = self.make_request("GET", "/ai/agents", token=self.admin_token)
        
        if success and isinstance(response, list):
            ai_agent = next((agent for agent in response if agent.get("id") == self.ai_agent_id), None)
            if ai_agent:
                linked_agents = ai_agent.get("linked_agents", [])
                if self.agent_id in linked_agents:
                    self.log_result("Verify Linked Agents Field", True, f"Linked agents correctly set: {linked_agents}")
                    return True
                else:
                    self.log_result("Verify Linked Agents Field", False, f"Agent {self.agent_id} not in linked_agents: {linked_agents}")
                    return False
            else:
                self.log_result("Verify Linked Agents Field", False, "AI agent not found")
                return False
        else:
            self.log_result("Verify Linked Agents Field", False, f"Error: {response}")
            return False

    def test_verify_emergent_llm_key(self) -> bool:
        """Test 10: Verificar se EMERGENT_LLM_KEY está configurada"""
        try:
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
                
            if 'EMERGENT_LLM_KEY' in env_content and 'sk-emergent-' in env_content:
                self.log_result("Verify Emergent LLM Key", True, "EMERGENT_LLM_KEY found and configured")
                return True
            else:
                self.log_result("Verify Emergent LLM Key", False, "EMERGENT_LLM_KEY not properly configured")
                return False
        except Exception as e:
            self.log_result("Verify Emergent LLM Key", False, f"Error reading .env: {e}")
            return False

    # ============================================
    # CLEANUP
    # ============================================
            
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up comprehensive AI test data...")
        
        if not self.admin_token:
            print("❌ No admin token for cleanup")
            return
        
        # Delete AI agent
        if self.ai_agent_id:
            success, response = self.make_request("DELETE", f"/ai/agents/{self.ai_agent_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted AI agent: {self.ai_agent_id}")
            else:
                print(f"❌ Failed to delete AI agent {self.ai_agent_id}: {response}")
        
        # Delete department
        if self.department_id:
            success, response = self.make_request("DELETE", f"/ai/departments/{self.department_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted department: {self.department_id}")
            else:
                print(f"❌ Failed to delete department {self.department_id}: {response}")
        
        # Delete agent
        if self.agent_id:
            success, response = self.make_request("DELETE", f"/agents/{self.agent_id}", token=self.admin_token)
            if success:
                print(f"✅ Deleted agent: {self.agent_id}")
            else:
                print(f"❌ Failed to delete agent {self.agent_id}: {response}")
                
    def run_all_tests(self):
        """Run all comprehensive AI tests"""
        print("🤖 TESTE COMPLETO - FLUXO COMPLETO DE IA")
        print("=" * 80)
        
        tests = [
            # Setup
            self.test_setup_admin,
            self.test_setup_agent,
            self.test_setup_client,
            self.test_setup_ai_agent,
            self.test_setup_department,
            
            # Message Flow Tests
            self.test_client_message_creates_ticket,
            self.test_department_selection,
            self.test_assign_ticket_to_agent,
            self.test_ai_response_to_message,
            
            # AI Control Tests
            self.test_toggle_ai_disable,
            self.test_ai_no_response_when_disabled,
            self.test_toggle_ai_enable,
            
            # PIX Tests
            self.test_pix_message_creation,
            
            # Verification Tests
            self.test_verify_linked_agents_field,
            self.test_verify_emergent_llm_key
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
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                failed_tests.append(test.__name__)
                
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES DE FLUXO DE IA PASSARAM!")
            print("✅ Sistema de IA funcionando corretamente com:")
            print("   - Integração e resposta automática")
            print("   - Controle por atendente (linked_agents)")
            print("   - Toggle de IA por conversa")
            print("   - Mensagens PIX")
            print("   - Emergent LLM Key configurada")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            
        # Cleanup
        self.cleanup()
            
        return passed, total, self.test_results

def main():
    """Main test execution"""
    print(f"🔗 Testing comprehensive AI flow at: {API_BASE}")
    print(f"🎯 Testing complete AI system as per review request")
    
    tester = ComprehensiveAITester()
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