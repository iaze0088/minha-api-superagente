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
    pinned_user: Optional[str] = ""
    pinned_pass: Optional[str] = ""

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

class ConfigData(BaseModel):
    quick_blocks: List[QuickBlock] = []
    auto_reply: List[AutoReply] = []
    apps: List[AppItem] = []

# Reseller Models
class ResellerBase(BaseModel):
    name: str
    email: str
    domain: Optional[str] = ""
    custom_domain: Optional[str] = ""
    is_active: bool = True

class ResellerCreate(BaseModel):
    name: str
    email: str
    password: str
    domain: Optional[str] = ""

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

# Notice Models
class NoticeBase(BaseModel):
    kind: MessageKind
    text: Optional[str] = ""
    file_url: Optional[str] = ""

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
