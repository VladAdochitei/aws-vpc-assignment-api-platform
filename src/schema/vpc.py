# src/schema/vpc.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VPCCreateRequest(BaseModel):
    vpc_name: str
    cidr_block: str
    region: str


class VPCUpdateRequest(BaseModel):
    vpc_name: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    # cidr_block intentionally omitted — see note below


class VPCResponse(BaseModel):
    vpc_id: str
    vpc_name: str
    cidr_block: str
    region: str
    created_by: Optional[str] = None
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


class VPCListResponse(BaseModel):
    items: list[VPCResponse]
    count: int