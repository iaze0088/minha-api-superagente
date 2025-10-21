from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

class TicketStatus(str, Enum):
    EM_ESPERA = "EM_ESPERA"
    ATENDENDO = "ATENDENDO"
    FINALIZADAS = "FINALIZADAS"

class MessageKind(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    audio = "audio"
    file = "file"
    pix = "pix"

class UserType(str, Enum):
    client = "client"
    agent = "agent"

# User Models
class UserBase(BaseModel):
    whatsapp: str
    display_name: Optional[str] = ""
    avatar: Optional[str] = ""
    custom_avatar: Optional[str] = ""
    gender: Optional[str] = ""
    pinned_user: Optional[str] = ""  # Credenciais PRIVADAS do cliente
    pinned_pass: Optional[str] = ""  # Credenciais PRIVADAS do cliente
    whatsapp_confirmed: Optional[str] = ""  # WhatsApp confirmado pelo cliente
    whatsapp_asked_at: Optional[str] = ""  # Última vez que perguntou WhatsApp
    name_asked_at: Optional[str] = ""  # Última vez que perguntou o nome
    reseller_id: Optional[str] = None  # Tenant isolation

class UserCreate(BaseModel):
    whatsapp: str
    pin: str

class UserLogin(BaseModel):
    whatsapp: str
    pin: str

class UserInDB(UserBase):
    id: str
    pin_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(UserBase):
    id: str
    created_at: datetime

# Agent Models
class AgentBase(BaseModel):
    name: str
    login: str
    avatar: Optional[str] = ""
    custom_avatar: Optional[str] = ""
    department_ids: List[str] = []  # Lista de departamentos que o atendente pode acessar
    reseller_id: Optional[str] = None  # Tenant isolation

class AgentCreate(BaseModel):
    name: str
    login: str
    password: str
    avatar: Optional[str] = ""
    department_ids: List[str] = []  # Departamentos do atendente

class AgentLogin(BaseModel):
    login: str
    password: str

class AgentInDB(AgentBase):
    id: str
    pass_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResponse(AgentBase):
    id: str
    created_at: datetime

# Ticket Models
class TicketBase(BaseModel):
    client_id: str
    status: TicketStatus = TicketStatus.EM_ESPERA
    department_id: Optional[str] = None  # Departamento do ticket
    awaiting_department_choice: bool = True  # Se está aguardando cliente escolher departamento
    department_choice_sent_at: Optional[str] = None  # Quando enviou a escolha de departamento
    unread_count: int = 0  # Contador de mensagens não lidas
    reseller_id: Optional[str] = None  # Tenant isolation

class TicketInDB(TicketBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TicketResponse(TicketBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Message Models
class MessageBase(BaseModel):
    ticket_id: str
    from_type: UserType
    from_id: str
    to_type: UserType
    to_id: str
    kind: MessageKind
    text: Optional[str] = ""
    file_url: Optional[str] = ""
    reseller_id: Optional[str] = None  # Tenant isolation

class MessageCreate(BaseModel):
    ticket_id: Optional[str] = None  # Optional for client messages (auto-created)
    from_type: UserType
    from_id: str
    to_type: UserType
    to_id: str
    kind: MessageKind
    text: Optional[str] = ""
    file_url: Optional[str] = ""
    reseller_id: Optional[str] = None

class MessageInDB(MessageBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageResponse(MessageBase):
    id: str
    created_at: datetime

# Config Models
class QuickBlock(BaseModel):
    name: str
    text: str

class AutoReply(BaseModel):
    q: str
    a: str

# Novo modelo para Auto-Responder Avançado
class AutoResponseItem(BaseModel):
    id: str  # UUID único
    type: str  # "text", "audio", "video", "photo"
    content: str  # Texto ou URL do arquivo
    delay: int = 0  # Delay em segundos (0-60)

class AutoResponderSequence(BaseModel):
    id: str  # UUID único da sequência
    trigger: str  # Palavra-chave que aciona a sequência
    responses: List[AutoResponseItem] = []  # Lista de respostas sequenciais
    enabled: bool = True
    reseller_id: Optional[str] = None  # Tenant isolation

# Novo modelo para Tutorials/Aplicativos Avançado
class TutorialItem(BaseModel):
    id: str  # UUID único
    type: str  # "text", "audio", "video", "photo"
    content: str  # Texto ou URL do arquivo
    delay: int = 0  # Delay em segundos (0-60)

class Tutorial(BaseModel):
    id: str  # UUID único do tutorial
    category: str  # Categoria (ex: "Setup", "Uso", "FAQ")
    title: str  # Título do tutorial
    items: List[TutorialItem] = []  # Lista de itens sequenciais
    enabled: bool = True
    reseller_id: Optional[str] = None  # Tenant isolation

class AppItem(BaseModel):
    cat: str
    title: str
    content: str

class AllowedData(BaseModel):
    cpfs: List[str] = []
    emails: List[str] = []
    phones: List[str] = []
    random_keys: List[str] = []

class APIIntegration(BaseModel):
    api_url: str = ""
    api_token: str = ""
    api_enabled: bool = False

class AIAgentConfig(BaseModel):
    name: str = "Assistente IA"
    personality: str = ""
    instructions: str = ""
    llm_provider: str = "openai"  # openai, claude, gemini
    llm_model: str = "gpt-4"
    api_key: Optional[str] = ""  # API Key do provedor LLM
    temperature: float = 0.7
    max_tokens: int = 500
    mode: str = "standby"  # standby, solo, hybrid
    active_hours: str = "24/7"  # Ex: "09:00-18:00" ou "24/7"
    enabled: bool = False
    can_access_credentials: bool = True
    knowledge_base: str = ""  # Texto ou instruções adicionais

class ConfigData(BaseModel):
    quick_blocks: List[QuickBlock] = []
    auto_reply: List[AutoReply] = []
    apps: List[AppItem] = []
    pix_key: Optional[str] = ""
    allowed_data: AllowedData = AllowedData()
    api_integration: APIIntegration = APIIntegration()
    ai_agent: AIAgentConfig = AIAgentConfig()
    reseller_id: Optional[str] = None  # Tenant isolation - cada revenda tem suas configs

# Reseller Models
class ResellerBase(BaseModel):
    name: str
    email: str
    domain: Optional[str] = ""
    custom_domain: Optional[str] = ""
    is_active: bool = True
    parent_id: Optional[str] = None  # ID da revenda pai (None se for raiz)
    level: int = 0  # Profundidade na hierarquia (0 = raiz)

class ResellerCreate(BaseModel):
    name: str
    email: str
    password: str
    domain: Optional[str] = ""
    parent_id: Optional[str] = None

class ResellerLogin(BaseModel):
    email: str
    password: str

class ResellerInDB(ResellerBase):
    id: str
    pass_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResellerResponse(ResellerBase):
    id: str
    created_at: datetime
    children_count: int = 0  # Número de sub-revendas

class ResellerTransfer(BaseModel):
    reseller_id: str
    new_parent_id: Optional[str] = None  # None = tornar raiz

# Notice Models
class NoticeBase(BaseModel):
    kind: MessageKind
    text: Optional[str] = ""
    file_url: Optional[str] = ""
    reseller_id: Optional[str] = None  # Tenant isolation

class NoticeCreate(NoticeBase):
    pass

class NoticeInDB(NoticeBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoticeResponse(NoticeBase):
    id: str
    created_at: datetime

# Admin Login
class AdminLogin(BaseModel):
    password: str

# Token Response
class TokenResponse(BaseModel):
    token: str
    user_type: str
    user_data: dict
    reseller_id: Optional[str] = None


# ============================================
# SISTEMA DE MÚLTIPLOS AGENTES IA
# ============================================

class AIAgentFull(BaseModel):
    """Modelo completo de Agente IA (similar ao SuperAgentes)"""
    id: str
    name: str
    description: Optional[str] = ""
    
    # Configurações do Prompt
    who_is: Optional[str] = ""  # Quem é o seu Agente?
    what_does: Optional[str] = ""  # O que seu Agente faz?
    objective: Optional[str] = ""  # Qual o objetivo do seu Agente?
    how_respond: Optional[str] = ""  # Como seu Agente deve responder?
    
    # Regras Gerais
    instructions: Optional[str] = ""  # Instruções para o Agente
    avoid_topics: Optional[str] = ""  # Quais temas ele deve evitar?
    avoid_words: Optional[str] = ""  # Quais palavras ele deve evitar?
    allowed_links: Optional[str] = ""  # Links permitidos
    custom_rules: Optional[str] = ""  # Regras personalizadas
    
    # Base de Conhecimento
    knowledge_base: Optional[str] = ""
    
    # Configurações do Modelo
    llm_provider: str = "openai"  # openai, claude, gemini
    llm_model: str = "gpt-4o-mini"
    api_key: Optional[str] = ""
    temperature: float = 0.5
    max_tokens: int = 500
    
    # Comportamento
    auto_detect_language: bool = True
    knowledge_restriction: bool = False
    timezone: str = "America/Sao_Paulo"
    response_delay_seconds: int = 3  # Tempo de espera antes de responder (0-60 segundos)
    
    # Status
    is_active: bool = True
    
    # Atendentes vinculados (IDs dos atendentes que têm esta IA ativa)
    linked_agents: List[str] = []
    
    # Tenant
    reseller_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIAgentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

class AIAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    who_is: Optional[str] = None
    what_does: Optional[str] = None
    objective: Optional[str] = None
    how_respond: Optional[str] = None
    instructions: Optional[str] = None
    avoid_topics: Optional[str] = None
    avoid_words: Optional[str] = None
    allowed_links: Optional[str] = None
    custom_rules: Optional[str] = None
    knowledge_base: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    auto_detect_language: Optional[bool] = None
    knowledge_restriction: Optional[bool] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    linked_agents: Optional[List[str]] = None

# ============================================
# SISTEMA DE DEPARTAMENTOS
# ============================================

class Department(BaseModel):
    """Departamento para roteamento (Suporte, Vendas, etc)"""
    id: str
    name: str
    description: Optional[str] = ""
    ai_agent_id: Optional[str] = None  # Agente IA vinculado a este departamento
    is_default: bool = False  # Departamento padrão (após timeout)
    timeout_seconds: int = 120  # Tempo para auto-direcionar (padrão: 2 min)
    reseller_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    ai_agent_id: Optional[str] = None
    is_default: bool = False
    timeout_seconds: int = 120

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ai_agent_id: Optional[str] = None
    is_default: Optional[bool] = None
    timeout_seconds: Optional[int] = None
