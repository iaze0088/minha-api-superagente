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
    reseller_id: Optional[str] = None  # Tenant isolation

class AgentCreate(BaseModel):
    name: str
    login: str
    password: str
    avatar: Optional[str] = ""

class AgentLogin(BaseModel):
    login: str
    password: str

class AgentInDB(AgentBase):
    id: str
    pass_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResponse(AgentBase):
    id: str
    created_at: datetime

# Ticket Models
class TicketBase(BaseModel):
    client_id: str
    status: TicketStatus = TicketStatus.EM_ESPERA
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

class MessageCreate(MessageBase):
    pass

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
