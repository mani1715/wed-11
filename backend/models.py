from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class WeddingStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class CreditTransactionType(str, Enum):
    CREDIT = "CREDIT"
    DEDUCT = "DEDUCT"

class AdminRole(str, Enum):
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

# Admin Models
class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    full_name: str
    role: AdminRole = AdminRole.ADMIN
    available_credits: int = 100  # Default starting credits
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: Optional[AdminRole] = AdminRole.ADMIN

class AdminLogin(BaseModel):
    email: str
    password: str

class AdminResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: AdminRole
    available_credits: int
    created_at: datetime

# Wedding Models
class Wedding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    title: str
    slug: str
    status: WeddingStatus = WeddingStatus.DRAFT
    selected_design_key: Optional[str] = None
    selected_features: List[str] = Field(default_factory=list)
    total_credit_cost: int = 0
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WeddingCreate(BaseModel):
    title: str
    slug: str

    @validator('slug')
    def validate_slug(cls, v):
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class WeddingUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    selected_design_key: Optional[str] = None
    selected_features: Optional[List[str]] = None
    status: Optional[WeddingStatus] = None

    @validator('slug')
    def validate_slug(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower() if v else v

class WeddingResponse(BaseModel):
    id: str
    admin_id: str
    title: str
    slug: str
    status: WeddingStatus
    selected_design_key: Optional[str]
    selected_features: List[str]
    total_credit_cost: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class PublishRequest(BaseModel):
    wedding_id: str

# Credit Models
class CreditLedger(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    transaction_type: CreditTransactionType
    amount: int
    balance_after: int
    description: str
    wedding_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CreditEstimation(BaseModel):
    design_cost: int
    features_cost: int
    total_cost: int
    breakdown: dict

class CreditConfig(BaseModel):
    designs: dict = {
        "basic": 10,
        "elegant": 20,
        "luxury": 30,
        "royal": 50
    }
    features: dict = {
        "rsvp": 5,
        "gallery": 10,
        "guestbook": 5,
        "countdown": 3,
        "music": 5,
        "video": 15,
        "live_streaming": 25,
        "gift_registry": 10
    }