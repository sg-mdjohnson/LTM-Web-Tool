from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.core.validators import validate_domain

class DNSLookupRequest(BaseModel):
    domain: str
    record_type: str = Field(..., regex="^(A|AAAA|MX|NS|TXT|CNAME|SOA|PTR)$")
    dns_server: Optional[str] = None

    @validator("domain")
    def validate_domain_name(cls, v):
        if not validate_domain(v):
            raise ValueError("Invalid domain name format")
        return v

class DNSRecord(BaseModel):
    name: str
    type: str
    ttl: int
    value: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DNSResponse(BaseModel):
    request_id: str
    domain: str
    record_type: str
    records: List[DNSRecord]
    query_time: float
    dns_server: Optional[str]
    status: str = "success"
    error: Optional[str] = None 