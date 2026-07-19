from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SubnetCreateRequest(BaseModel):
    subnet_name: str
    cidr_block: str
    availability_zone: Optional[str] = None


class SubnetUpdateRequest(BaseModel):
    subnet_name: Optional[str] = None
    status: Optional[str] = None
    # cidr_block and availability_zone omitted — immutable in AWS, same reasoning as VPC's cidr_block


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