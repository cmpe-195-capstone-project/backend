from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class ResourceType(str, Enum):
    SHELTER = "shelter"
    HOUSING = "housing"
    HOTLINE = "hotline"
    INFORMATION = "information"
    FOOD_ASSISTANCE = "food_assistance"
    SOCIAL_SERVICES = "social_services"
    MULTI_SERVICE = "multi_service"

class PhoneType(str, Enum):
    MAIN = "main"
    HOTLINE = "hotline"
    CRISIS = "crisis"
    INFO = "info"
    TTY = "tty"
    ALT = "alt"

class ContactPhone(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: PhoneType = Field(default=PhoneType.MAIN)
    number: str
    e164: Optional[str] = None
    notes: Optional[str] = None

class Address(BaseModel):
    model_config = ConfigDict(frozen=True)
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    county: Optional[str] = None

class Hours(BaseModel):
    model_config = ConfigDict(frozen=True)
    open_24_7: Optional[bool] = None
    plain_text: Optional[str] = None

class ResourcePlaceSchema(BaseModel):
    id: str
    name: str
    resource_type: ResourceType
    subcategory: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[str]] = None
    service_areas: Optional[List[str]] = None
    address: Optional[Address] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phones: List[ContactPhone] = Field(default_factory=list)
    website_url: Optional[str] = None
    source_url: Optional[str] = None
    hours: Optional[Hours] = None
    eligibility: Optional[str] = None
    emergency_only: Optional[bool] = None
    accepts_pets: Optional[bool] = None
    accepts_rv: Optional[bool] = None
    capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    inserted_at: Optional[datetime] = None
    last_verified: Optional[datetime] = None

    model_config = ConfigDict(frozen=True, from_attributes=True)
