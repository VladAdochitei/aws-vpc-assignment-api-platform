from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class VPC:
    vpc_id: str
    vpc_name: str
    cidr_block: str
    region: str
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"

    def key(self) -> dict:
        return {"PK": f"VPC#{self.vpc_id}", "SK": f"VPC#{self.vpc_id}"}

    def to_item(self) -> dict:
        return {**self.key(), "entity_type": "vpc", **self.__dict__}