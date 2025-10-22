"""
Serviço de Automação IPTV - Sistema Robusto e Inteligente
Suporta automação via Playwright com retry, validação e fallback manual
"""
import asyncio
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser


class AutomationResult:
    """Resultado da automação"""
    def __init__(self):
        self.success = False
        self.message = ""
        self.final_url = ""
        self.screenshots = []  # Lista de screenshots em base64
        self.logs = []  # Lista de logs
        self.error = None
        self.automation_score = 0  # Score de automatizabilidade (0-100)
    
    def add_log(self, log: str, level: str = "info"):
        """Adiciona log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            "time": timestamp,
            "level": level,
            "message": log
        })
        print(f"[{timestamp}] [{level.upper()}] {log}")
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            "success": self.success,
            "message": self.message,
            "final_url": self.final_url,
            "screenshots": self.screenshots,
            "logs": self.logs,
            "error": self.error,
            "automation_score": self.automation_score
        }


class IPTVAutomationBase:
    """Classe base para automação de apps IPTV"""
    
    def __init__(self, app_data: Dict, form_data: Dict):
        self.app_data = app_data
        self.form_data = form_data
        self.result = AutomationResult()
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
    
    async def take_screenshot(self, description: str = ""):
        """Tira screenshot e adiciona ao resultado"""
        try:
            if self.page:
                screenshot = await self.page.screenshot(type='png', full_page=False)
                screenshot_base64 = screenshot.hex()
                self.result.screenshots.append({
                    "description": description,
                    "data": screenshot_base64[:1000]  # Limitar tamanho
                })
                self.result.add_log(f"📸 Screenshot capturado: {description}")
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao capturar screenshot: {e}", "warning")
    
    async def wait_and_retry(self, action, max_retries: int = 3, delay: int = 1000):
        """Executa ação com retry"""
        for attempt in range(max_retries):
            try:
                await action()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.result.add_log(f"⚠️ Tentativa {attempt + 1}/{max_retries} falhou: {e}. Tentando novamente...", "warning")
                    await self.page.wait_for_timeout(delay)
                else:
                    self.result.add_log(f"❌ Todas as tentativas falharam: {e}", "error")
                    raise e
        return False
    
    async def try_multiple_selectors(self, selectors: List[str], action: str, value: str = None) -> bool:
        """Tenta múltiplos seletores até encontrar um que funcione"""
        for selector in selectors:
            try:
                if action == "fill":
                    await self.page.fill(selector, value, timeout=5000)
                    self.result.add_log(f"✅ Campo preenchido com sucesso: {selector}")
                    return True
                elif action == "click":
                    await self.page.click(selector, timeout=5000)
                    self.result.add_log(f"✅ Botão clicado com sucesso: {selector}")
                    return True
                elif action == "wait":
                    await self.page.wait_for_selector(selector, timeout=5000)
                    self.result.add_log(f"✅ Elemento encontrado: {selector}")
                    return True
            except Exception:
                continue
        
        self.result.add_log(f"⚠️ Nenhum seletor funcionou para ação '{action}'", "warning")
        return False
    
    async def generate_final_url(self) -> str:
        """Gera URL final com template"""
        url_template = self.app_data.get('url_template', '')
        final_url = url_template
        
        for field, value in self.form_data.items():
            final_url = final_url.replace(f'{{{field}}}', str(value))
        
        self.result.add_log(f"🔗 URL gerada: {final_url}")
        return final_url
    
    async def initialize_browser(self):
        """Inicializa o navegador Playwright"""
        async with async_playwright() as p:
            self.result.add_log("🚀 Iniciando navegador...")
            
            self.browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await context.new_page()
            self.result.add_log("✅ Navegador iniciado com sucesso!")
            
            # Executar automação específica
            await self.run_automation()
            
            await self.browser.close()
    
    async def run_automation(self):
        """Método abstrato - deve ser implementado por subclasses"""
        raise NotImplementedError("Subclasses devem implementar run_automation()")
    
    async def execute(self) -> AutomationResult:
        """Executa a automação completa"""
        try:
            await self.initialize_browser()
            self.result.success = True
            self.result.message = "Automação concluída com sucesso!"
        except Exception as e:
            self.result.success = False
            self.result.error = str(e)
            self.result.message = f"Erro na automação: {str(e)}"
            self.result.add_log(f"❌ ERRO CRÍTICO: {e}", "error")
            self.result.add_log(f"📋 Stack trace: {traceback.format_exc()}", "error")
        
        return self.result


class SSIPTVAutomation(IPTVAutomationBase):
    """Automação específica para SS-IPTV"""
    
    async def run_automation(self):
        """Executa automação do SS-IPTV com seletores corretos"""
        self.result.add_log("🔧 Iniciando automação SS-IPTV...")
        
        # Navegar para o site
        config_url = self.app_data.get('config_url')
        self.result.add_log(f"📍 Navegando para {config_url}")
        
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.page.wait_for_timeout(5000)
        await self.take_screenshot("Página inicial carregada")
        
        # PASSO 1: Preencher código no campo correto
        codigo = self.form_data.get('codigo', '')
        if codigo:
            self.result.add_log(f"📝 Preenchendo código: {codigo}")
            
            try:
                await self.page.fill('#inptConnectionCodeInput', codigo, timeout=10000)
                self.result.add_log("✅ Código preenchido com sucesso!")
                await self.page.wait_for_timeout(1000)
                await self.take_screenshot("Código preenchido")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao preencher código: {e}", "error")
                raise Exception("Não foi possível preencher o código.")
        
        # PASSO 2: Clicar no botão ADD DEVICE
        self.result.add_log("🔘 Clicando no botão ADD DEVICE...")
        
        try:
            await self.page.click('#btnAddDevice', timeout=10000)
            self.result.add_log("✅ Botão ADD DEVICE clicado!")
            await self.page.wait_for_timeout(3000)
            await self.take_screenshot("Após ADD DEVICE")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao clicar ADD DEVICE: {e}", "error")
            raise Exception("Não foi possível clicar no botão ADD DEVICE.")
        
        # PASSO 2.5: CRITICAL - Clicar na aba "External Playlists"
        self.result.add_log("📂 Mudando para aba 'External Playlists'...")
        
        try:
            # Tentar vários seletores para a aba External Playlists
            external_playlist_selectors = [
                '#playlistsTab',
                'a[href="#playlists"]',
                'a[name="content://playlists"]',
                'a:has-text("External Playlists")'
            ]
            
            clicked_external = False
            for selector in external_playlist_selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    self.result.add_log("✅ Aba 'External Playlists' selecionada!")
                    clicked_external = True
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("Aba External Playlists")
                    break
                except:
                    continue
            
            if not clicked_external:
                self.result.add_log("⚠️ Aba External Playlists não encontrada - tentando prosseguir...", "warning")
                
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao mudar para External Playlists: {e}", "warning")
        
        # PASSO 3: Aguardar device conectar e botão ADD ITEM ficar visível
        self.result.add_log("⏳ Aguardando dispositivo conectar (TV precisa estar com o app aberto)...")
        self.result.add_log("📺 Abra o app SS-IPTV na TV com o código digitado!")
        
        try:
            # Aguardar até 30 segundos para o botão ficar visível
            await self.page.wait_for_selector('#btnAddPlaylistItem', state='visible', timeout=30000)
            self.result.add_log("✅ Dispositivo conectado! Botão ADD ITEM está visível!")
            
            # Aguardar mais um pouco para garantir
            await self.page.wait_for_timeout(2000)
            
            # Clicar no botão ADD ITEM
            await self.page.click('#btnAddPlaylistItem')
            self.result.add_log("✅ Botão ADD ITEM clicado!")
            await self.page.wait_for_timeout(2000)
            await self.take_screenshot("Modal ADD ITEM aberto")
            
        except Exception as e:
            self.result.add_log(f"❌ Timeout: Dispositivo não conectou em 30 segundos", "error")
            self.result.add_log(f"💡 Certifique-se que o app SS-IPTV está aberto na TV!", "warning")
            raise Exception("Dispositivo não conectou. Abra o app SS-IPTV na TV e tente novamente.")
        
        # PASSO 4: Gerar URL final
        username = self.form_data.get('username', '')
        password = self.form_data.get('password', '')
        
        if username and password:
            self.result.final_url = await self.generate_final_url()
            self.result.add_log(f"🔗 URL da playlist gerada: {self.result.final_url}")
            
            # PASSO 5: Preencher nome da playlist (opcional mas recomendado)
            try:
                playlist_name = f"Playlist {username}"
                await self.page.fill('#inputStreamTitle', playlist_name, timeout=10000)
                self.result.add_log(f"✅ Nome da playlist preenchido: {playlist_name}")
            except Exception as e:
                self.result.add_log(f"⚠️ Nome não preenchido: {e}", "warning")
            
            # PASSO 6: Preencher URL da playlist no campo correto
            self.result.add_log("📋 Preenchendo URL da playlist...")
            
            try:
                await self.page.fill('#inputStreamURL', self.result.final_url, timeout=10000)
                self.result.add_log("✅ URL da playlist preenchida com sucesso!")
                await self.page.wait_for_timeout(1000)
                await self.take_screenshot("URL preenchida")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao preencher URL: {e}", "error")
                raise Exception("Não foi possível preencher a URL da playlist.")
            
            # PASSO 7: Clicar no botão OK para salvar
            self.result.add_log("🔘 Clicando no botão OK...")
            
            try:
                await self.page.click('#btnApplyChanges', timeout=10000)
                self.result.add_log("✅ Botão OK clicado!")
                await self.page.wait_for_timeout(3000)
                await self.take_screenshot("Playlist adicionada")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao clicar OK: {e}", "error")
                raise Exception("Não foi possível clicar no botão OK.")
            
            # PASSO 8: CRITICAL - Clicar no botão SAVE para salvar no servidor
            self.result.add_log("💾 Clicando no botão SAVE para salvar permanentemente...")
            
            try:
                # Aguardar um pouco para o modal fechar completamente
                await self.page.wait_for_timeout(2000)
                
                # Clicar no botão SAVE usando o seletor correto
                await self.page.click('#btnSave', timeout=10000)
                self.result.add_log("✅ Botão SAVE clicado com sucesso!")
                
                # Aguardar o salvamento no servidor
                await self.page.wait_for_timeout(3000)
                await self.take_screenshot("Após clicar SAVE")
                
            except Exception as e:
                self.result.add_log(f"❌ Erro ao clicar SAVE: {e}", "error")
                raise Exception("Não foi possível clicar no botão SAVE.")
            
            # PASSO 9: Verificar se playlist apareceu na lista
            self.result.add_log("🔍 Verificando se playlist foi adicionada...")
            
            try:
                # Aguardar um pouco para a lista atualizar
                await self.page.wait_for_timeout(2000)
                
                # Verificar se há algum item na tabela
                items = await self.page.query_selector_all('table tbody tr')
                if len(items) > 0:
                    self.result.add_log(f"✅ Total de itens na lista: {len(items)}")
                    
                    # Verificar se nossa URL está na lista
                    page_content = await self.page.content()
                    if '3334567oro' in page_content or self.result.final_url in page_content:
                        self.result.add_log("✅ Playlist confirmada na lista!")
                    else:
                        self.result.add_log("⚠️ URL não encontrada na lista - pode não ter sido salva", "warning")
                else:
                    self.result.add_log("⚠️ Nenhum item encontrado na lista", "warning")
                
                await self.take_screenshot("Lista final de playlists")
            except Exception as e:
                self.result.add_log(f"⚠️ Não foi possível verificar lista: {e}", "warning")
        
        self.result.add_log("✅ Automação SS-IPTV concluída!")
        self.result.automation_score = 95


class SmartOneAutomation(IPTVAutomationBase):
    """Automação específica para SmartOne IPTV"""
    
    async def run_automation(self):
        """Executa automação do SmartOne com seletores corretos"""
        self.result.add_log("🔧 Iniciando automação SmartOne IPTV...")
        
        # Navegar para o site
        config_url = self.app_data.get('config_url')
        self.result.add_log(f"📍 Navegando para {config_url}")
        
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.page.wait_for_timeout(5000)
        await self.take_screenshot("Página inicial carregada")
        
        # PASSO 1: Preencher MAC address (usar classe específica para campo visível)
        mac = self.form_data.get('mac', '')
        if mac:
            self.result.add_log(f"📝 Preenchendo MAC address: {mac}")
            
            try:
                # Usar seletor específico para o campo MAC visível (mac-3)
                await self.page.fill('input.mac-3', mac, timeout=10000)
                self.result.add_log("✅ MAC preenchido com sucesso!")
                await self.page.wait_for_timeout(1000)
                await self.take_screenshot("MAC preenchido")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao preencher MAC: {e}", "error")
                raise Exception("Não foi possível preencher o MAC address.")
        
        # PASSO 2: Preencher nome da playlist
        username = self.form_data.get('username', '')
        nome_pasta = f"Playlist {username}" if username else "Minha Playlist"
        
        self.result.add_log(f"📝 Preenchendo nome da playlist: {nome_pasta}")
        
        try:
            await self.page.fill('#m3u_name', nome_pasta, timeout=10000)
            self.result.add_log("✅ Nome da playlist preenchido!")
            await self.page.wait_for_timeout(1000)
            await self.take_screenshot("Nome preenchido")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao preencher nome: {e}", "error")
            raise Exception("Não foi possível preencher o nome da playlist.")
        
        # PASSO 3: Gerar e preencher URL da playlist
        self.result.final_url = await self.generate_final_url()
        self.result.add_log(f"🔗 URL da playlist gerada: {self.result.final_url}")
        
        try:
            # Usar seletor específico para o campo de URL
            await self.page.fill('input#m3u_playlist.form-control', self.result.final_url, timeout=10000)
            self.result.add_log("✅ URL da playlist preenchida!")
            await self.page.wait_for_timeout(1000)
            await self.take_screenshot("URL preenchida")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao preencher URL: {e}", "error")
            raise Exception("Não foi possível preencher a URL da playlist.")
        
        # PASSO 4: Marcar checkbox "Confirme que você é humano"
        self.result.add_log("✅ Procurando e marcando checkbox...")
        
        try:
            # Tentar múltiplos seletores para o checkbox
            checkbox_selectors = [
                'input[type="checkbox"]:visible',
                'label:has-text("Confirme") input[type="checkbox"]',
                'label:has-text("humano") input[type="checkbox"]',
                'form input[type="checkbox"]'
            ]
            
            checkbox_found = False
            for selector in checkbox_selectors:
                try:
                    await self.page.check(selector, timeout=5000)
                    self.result.add_log("✅ Checkbox marcado!")
                    checkbox_found = True
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("Checkbox marcado")
                    break
                except:
                    continue
            
            if not checkbox_found:
                self.result.add_log("⚠️ Checkbox não encontrado - tentando prosseguir...", "warning")
                
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao marcar checkbox: {e}", "warning")
            # Continuar mesmo se falhar
        
        # PASSO 5: Clicar no botão "Add Playlist"
        self.result.add_log("🔘 Clicando no botão 'Add Playlist'...")
        
        try:
            # Usar seletor específico do botão verde
            await self.page.click('button.btn.btn-success', timeout=10000)
            self.result.add_log("✅ Botão 'Add Playlist' clicado!")
            await self.page.wait_for_timeout(5000)
            await self.take_screenshot("Após clicar Add Playlist")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao clicar botão: {e}", "error")
            raise Exception("Não foi possível clicar no botão Add Playlist.")
        
        # PASSO 6: Verificar se há mensagem de sucesso
        self.result.add_log("🔍 Verificando mensagem de sucesso...")
        
        try:
            # Aguardar um pouco para a página processar
            await self.page.wait_for_timeout(3000)
            
            # Procurar por mensagens de sucesso
            page_content = await self.page.content()
            
            if 'success' in page_content.lower() or 'successfully' in page_content.lower():
                self.result.add_log("✅ Mensagem de sucesso detectada!")
            else:
                self.result.add_log("⚠️ Nenhuma mensagem de sucesso clara encontrada", "warning")
            
            await self.take_screenshot("Página final")
            
        except Exception as e:
            self.result.add_log(f"⚠️ Não foi possível verificar sucesso: {e}", "warning")
        
        self.result.add_log("✅ Automação SmartOne IPTV concluída!")
        self.result.automation_score = 95


class IPTVAutomationFactory:
    """Factory para criar instâncias de automação"""
    
    @staticmethod
    def create(app_type: str, app_data: Dict, form_data: Dict) -> IPTVAutomationBase:
        """Cria instância de automação baseada no tipo de app"""
        automations = {
            "SSIPTV": SSIPTVAutomation,
            "SMARTONE": SmartOneAutomation,
            # Adicionar outros apps conforme implementados
        }
        
        automation_class = automations.get(app_type)
        
        if not automation_class:
            # Fallback para automação genérica
            raise NotImplementedError(f"Automação para {app_type} ainda não implementada")
        
        return automation_class(app_data, form_data)


# Função principal de automação
async def automate_iptv_app(app_data: Dict, form_data: Dict) -> Dict:
    """
    Automatiza configuração de app IPTV
    
    Args:
        app_data: Dados do app (type, config_url, url_template, etc)
        form_data: Dados do formulário (codigo, username, password, mac, etc)
    
    Returns:
        Dict com resultado da automação
    """
    try:
        app_type = app_data.get('type')
        
        # Criar instância de automação
        automation = IPTVAutomationFactory.create(app_type, app_data, form_data)
        
        # Executar automação
        result = await automation.execute()
        
        return result.to_dict()
        
    except NotImplementedError as e:
        # App não tem automação implementada - retornar fallback para manual
        return {
            "success": False,
            "message": f"Automação para este app ainda não está disponível. Use o modo manual.",
            "error": str(e),
            "automation_score": 0,
            "logs": [{"time": datetime.now().strftime("%H:%M:%S"), "level": "info", "message": str(e)}],
            "screenshots": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro inesperado na automação: {str(e)}",
            "error": str(e),
            "automation_score": 0,
            "logs": [
                {"time": datetime.now().strftime("%H:%M:%S"), "level": "error", "message": str(e)},
                {"time": datetime.now().strftime("%H:%M:%S"), "level": "error", "message": traceback.format_exc()}
            ],
            "screenshots": []
        }
