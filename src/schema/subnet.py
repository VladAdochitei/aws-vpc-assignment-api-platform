# src/schema/subnet.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class SubnetCreateRequest(BaseModel):
    subnet_name: str
    cidr_block: str
    availability_zone: Optional[str] = None

    @field_validator("cidr_block")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        import ipaddress
        try:
            ipaddress.ip_network(v, strict=True)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR block: {v}") from e
        return v


class SubnetUpdateRequest(BaseModel):
    subnet_name: Optional[str] = None
    availability_zone: Optional[str] = None
    status: Optional[str] = None


class SubnetResponse(BaseModel):
    subnet_id: str
    vpc_id: str
    subnet_name: str
    cidr_block: str
    availability_zone: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


class SubnetListResponse(BaseModel):
    items: list[SubnetResponse]
    count: int