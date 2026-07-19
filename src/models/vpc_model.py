from dataclasses import dataclass, field, asdict
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

    def to_dict(self) -> dict:
        return asdict(self)

    def to_dynamodb(self) -> dict:
        return {**self.key(), "entity_type": "vpc", **self.to_dict()}

    @classmethod
    def from_dynamodb(cls, item: dict) -> "VPC":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})