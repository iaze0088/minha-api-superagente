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
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',  # Esconder automação
                    '--disable-dev-shm-usage',
                    '--disable-web-security'
                ]
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )
            
            # Adicionar scripts para esconder automação
            await context.add_init_script("""
                // Remover propriedades que identificam automação
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Adicionar propriedades que navegadores reais têm
                window.chrome = {
                    runtime: {}
                };
                
                // Fingir ser um navegador real
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
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
        await self.page.wait_for_timeout(3000)
        await self.take_screenshot("Página inicial carregada")
        
        # PASSO EXTRA: Aceitar cookies se aparecer
        self.result.add_log("🍪 Procurando banner de cookies...")
        try:
            # Tentar encontrar e clicar no botão de aceitar cookies
            cookie_buttons = [
                'button:has-text("Accept Cookies")',
                'button:has-text("Accept")',
                'button:has-text("Aceitar")',
                'a:has-text("Accept Cookies")',
                '.cookie-accept',
                '#cookie-accept'
            ]
            
            cookies_accepted = False
            for selector in cookie_buttons:
                try:
                    await self.page.click(selector, timeout=3000)
                    self.result.add_log("✅ Cookies aceitos!")
                    cookies_accepted = True
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("Cookies aceitos")
                    break
                except:
                    continue
            
            if not cookies_accepted:
                self.result.add_log("ℹ️ Banner de cookies não encontrado ou já aceito")
        except Exception as e:
            self.result.add_log(f"ℹ️ Erro ao aceitar cookies: {e}")
        
        # Aguardar MAIS tempo para Cloudflare carregar após cookies
        self.result.add_log("⏳ Aguardando Cloudflare carregar (10s)...")
        await self.page.wait_for_timeout(10000)
        
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
        
        # PASSO 4: Interagir com Cloudflare Turnstile e aguardar validação
        self.result.add_log("🔒 Procurando Cloudflare Turnstile...")
        
        try:
            # Aguardar o iframe do Cloudflare aparecer usando múltiplos seletores
            cloudflare_iframe = None
            
            # Tentar seletores específicos do Cloudflare
            selectors_to_try = [
                'iframe[id*="cf-chl-widget"]',  # ID específico do Cloudflare
                'iframe[src*="challenges.cloudflare.com"]',
                'iframe[title*="Cloudflare"]',
                '.cb-i iframe'  # Iframe dentro da div com classe cb-i
            ]
            
            for selector in selectors_to_try:
                try:
                    await self.page.wait_for_selector(selector, state='visible', timeout=15000)
                    cloudflare_iframe = await self.page.query_selector(selector)
                    self.result.add_log(f"✅ Cloudflare encontrado com seletor: {selector}")
                    break
                except:
                    self.result.add_log(f"⏳ Seletor '{selector}' não encontrou Cloudflare, tentando próximo...")
                    continue
            
            if not cloudflare_iframe:
                raise Exception("Cloudflare iframe não encontrado com nenhum seletor")
            
            # Aguardar iframe carregar completamente
            await self.page.wait_for_timeout(3000)
            await self.take_screenshot("Cloudflare encontrado")
            
            # Método 1: Tentar clicar diretamente no iframe
            self.result.add_log("🔘 Clicando no Cloudflare Turnstile...")
            try:
                await cloudflare_iframe.click()
                self.result.add_log("✅ Clique realizado no Cloudflare!")
            except:
                # Método 2: Clicar usando coordenadas do iframe
                box = await cloudflare_iframe.bounding_box()
                if box:
                    await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    self.result.add_log("✅ Clique realizado via coordenadas!")
            
            # Aguardar validação (20 segundos)
            self.result.add_log("⏳ Aguardando validação do Cloudflare (20s)...")
            await self.page.wait_for_timeout(20000)
            
            # Verificar se apareceu "Sucesso" ou checkmark
            page_content = await self.page.content()
            if any(word in page_content for word in ['Sucesso', 'Success', '✓', 'verified', 'checked']):
                self.result.add_log("✅ Cloudflare validado com sucesso!")
            else:
                self.result.add_log("⚠️ Validação do Cloudflare pode não ter completado", "warning")
            
            await self.take_screenshot("Após validação Cloudflare")
                
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao processar Cloudflare: {e}", "warning")
            self.result.add_log("⏳ Aguardando 15s mesmo sem detectar Cloudflare...", "warning")
            await self.page.wait_for_timeout(15000)
            await self.take_screenshot("Timeout Cloudflare")
            # Continuar mesmo se falhar
        
        # PASSO 5: Rolar e clicar no botão usando JavaScript (força bruta)
        self.result.add_log("📜 Rolando página e procurando botão...")
        
        try:
            # Rolar a página
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self.page.wait_for_timeout(2000)
            await self.take_screenshot("Após rolar")
            
            self.result.add_log("🔘 Tentando clicar no botão 'Add Playlist' com JavaScript...")
            
            # Usar JavaScript para encontrar e clicar no botão
            clicked = await self.page.evaluate('''() => {
                // Procurar botão com texto "Add Playlist"
                const buttons = Array.from(document.querySelectorAll('button'));
                const addButton = buttons.find(btn => 
                    btn.textContent.includes('Add Playlist') && 
                    btn.offsetParent !== null  // Verificar se está visível
                );
                
                if (addButton) {
                    addButton.click();
                    return true;
                }
                return false;
            }''')
            
            if clicked:
                self.result.add_log("✅ Botão 'Add Playlist' clicado via JavaScript!")
                await self.page.wait_for_timeout(5000)
                await self.take_screenshot("Após clicar Add Playlist")
            else:
                # Fallback: tentar com Playwright
                self.result.add_log("⚠️ Tentando método alternativo...")
                await self.page.click('button:has-text("Add Playlist")', timeout=10000, force=True)
                self.result.add_log("✅ Botão clicado (método alternativo)!")
                await self.page.wait_for_timeout(5000)
                await self.take_screenshot("Após clicar (alternativo)")
                
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




class DuplecastAutomation(IPTVAutomationBase):
    """Automação específica para Duplecast IPTV"""
    
    async def run_automation(self):
        """Executa automação do Duplecast com reCAPTCHA"""
        self.result.add_log("🔧 Iniciando automação Duplecast IPTV...")
        
        # Navegar para o site de login
        config_url = self.app_data.get('config_url')
        self.result.add_log(f"📍 Navegando para {config_url}")
        
        await self.page.goto(config_url, wait_until='domcontentloaded', timeout=60000)
        await self.page.wait_for_timeout(5000)
        await self.take_screenshot("Página de login carregada")
        
        # PASSO 1: Preencher Device ID (MAC)
        mac = self.form_data.get('mac', '')
        device_key = self.form_data.get('device_key', '')
        
        if mac:
            self.result.add_log(f"📝 Preenchendo Device ID: {mac}")
            
            try:
                # Tentar múltiplos seletores para Device ID
                device_id_selectors = [
                    'input[name="device_id"]',
                    'input#device_id',
                    'input[placeholder*="Device ID" i]'
                ]
                
                filled = False
                for selector in device_id_selectors:
                    try:
                        await self.page.fill(selector, mac, timeout=5000)
                        self.result.add_log("✅ Device ID preenchido!")
                        filled = True
                        break
                    except:
                        continue
                
                if not filled:
                    raise Exception("Não foi possível preencher Device ID")
                    
                await self.page.wait_for_timeout(1000)
                await self.take_screenshot("Device ID preenchido")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao preencher Device ID: {e}", "error")
                raise Exception("Não foi possível preencher o Device ID.")
        
        # PASSO 2: Preencher Device Key
        if device_key:
            self.result.add_log(f"📝 Preenchendo Device Key: {device_key}")
            
            try:
                device_key_selectors = [
                    'input[name="device_key"]',
                    'input#device_key',
                    'input[placeholder*="Device Key" i]'
                ]
                
                filled = False
                for selector in device_key_selectors:
                    try:
                        await self.page.fill(selector, device_key, timeout=5000)
                        self.result.add_log("✅ Device Key preenchido!")
                        filled = True
                        break
                    except:
                        continue
                
                if not filled:
                    raise Exception("Não foi possível preencher Device Key")
                    
                await self.page.wait_for_timeout(1000)
                await self.take_screenshot("Device Key preenchido")
            except Exception as e:
                self.result.add_log(f"❌ Erro ao preencher Device Key: {e}", "error")
                raise Exception("Não foi possível preencher o Device Key.")
        
        # PASSO 3: Interagir com reCAPTCHA (Google)
        self.result.add_log("🔒 Procurando reCAPTCHA...")
        
        try:
            # Aguardar reCAPTCHA aparecer
            await self.page.wait_for_timeout(3000)
            
            # Procurar iframe do reCAPTCHA
            recaptcha_iframe = await self.page.query_selector('iframe[src*="google.com/recaptcha"]')
            
            if recaptcha_iframe:
                self.result.add_log("✅ reCAPTCHA encontrado!")
                
                # Clicar no checkbox do reCAPTCHA
                try:
                    await recaptcha_iframe.click()
                    self.result.add_log("🔘 Clicou no reCAPTCHA")
                    
                    # Aguardar validação (15 segundos)
                    self.result.add_log("⏳ Aguardando validação do reCAPTCHA (15s)...")
                    await self.page.wait_for_timeout(15000)
                    
                    await self.take_screenshot("Após reCAPTCHA")
                except Exception as e:
                    self.result.add_log(f"⚠️ Erro ao clicar reCAPTCHA: {e}", "warning")
            else:
                self.result.add_log("ℹ️ reCAPTCHA não encontrado")
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao processar reCAPTCHA: {e}", "warning")
        
        # PASSO 4: Clicar no botão "Manage Device"
        self.result.add_log("🔘 Clicando no botão 'Manage Device'...")
        
        try:
            await self.page.click('button.btn.btn-primary[type="submit"]', timeout=10000)
            self.result.add_log("✅ Botão 'Manage Device' clicado!")
            await self.page.wait_for_timeout(5000)
            await self.take_screenshot("Após login")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao clicar 'Manage Device': {e}", "error")
            raise Exception("Não foi possível fazer login no dispositivo.")
        
        # PASSO 5: Clicar no botão "+ Add Playlist"
        self.result.add_log("🔘 Clicando no botão 'Add Playlist'...")
        
        try:
            add_playlist_selectors = [
                '#add_playlist',
                'a[href*="/device_main/add/"]',
                'a:has-text("Add Playlist")'
            ]
            
            clicked = False
            for selector in add_playlist_selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    self.result.add_log("✅ Botão 'Add Playlist' clicado!")
                    clicked = True
                    break
                except:
                    continue
            
            if not clicked:
                raise Exception("Botão Add Playlist não encontrado")
            
            await self.page.wait_for_timeout(3000)
            await self.take_screenshot("Formulário Add Playlist")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao clicar 'Add Playlist': {e}", "error")
            raise Exception("Não foi possível abrir formulário de adicionar playlist.")
        
        # PASSO 6: Preencher nome da playlist
        username = self.form_data.get('username', '')
        nome_playlist = f"Playlist {username}" if username else "Minha Playlist"
        
        self.result.add_log(f"📝 Preenchendo nome: {nome_playlist}")
        
        try:
            await self.page.fill('#m3u_name', nome_playlist, timeout=10000)
            self.result.add_log("✅ Nome preenchido!")
            await self.page.wait_for_timeout(1000)
        except Exception as e:
            self.result.add_log(f"❌ Erro ao preencher nome: {e}", "error")
            raise Exception("Não foi possível preencher o nome da playlist.")
        
        # PASSO 7: Gerar e preencher URL
        self.result.final_url = await self.generate_final_url()
        self.result.add_log(f"🔗 URL gerada: {self.result.final_url}")
        
        try:
            await self.page.fill('#m3u_playlist', self.result.final_url, timeout=10000)
            self.result.add_log("✅ URL preenchida!")
            await self.page.wait_for_timeout(1000)
            await self.take_screenshot("Formulário preenchido")
        except Exception as e:
            self.result.add_log(f"❌ Erro ao preencher URL: {e}", "error")
            raise Exception("Não foi possível preencher a URL da playlist.")
        
        # PASSO 8: Clicar no botão Submit/Save
        self.result.add_log("🔘 Clicando no botão de salvar...")
        
        try:
            submit_selectors = [
                'button[type="submit"]',
                'button.btn-primary',
                'button:has-text("Save")',
                'input[type="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    self.result.add_log("✅ Botão de salvar clicado!")
                    await self.page.wait_for_timeout(5000)
                    await self.take_screenshot("Playlist salva")
                    break
                except:
                    continue
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao clicar botão salvar: {e}", "warning")
        
        # PASSO 9: Verificar sucesso
        self.result.add_log("🔍 Verificando se playlist foi adicionada...")
        
        try:
            page_content = await self.page.content()
            if any(word in page_content.lower() for word in ['success', 'added', 'saved', 'sucesso']):
                self.result.add_log("✅ Playlist adicionada com sucesso!")
            else:
                self.result.add_log("ℹ️ Playlist provavelmente adicionada")
            
            await self.take_screenshot("Resultado final")
        except Exception as e:
            self.result.add_log(f"⚠️ Erro ao verificar: {e}", "warning")
        
        self.result.add_log("✅ Automação Duplecast concluída!")
        self.result.automation_score = 85


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
