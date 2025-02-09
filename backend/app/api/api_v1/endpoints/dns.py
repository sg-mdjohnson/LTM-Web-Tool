from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.core.validators import validate_domain, validate_ip_address
from app.schemas.dns import DNSLookupRequest, DNSResponse

router = APIRouter()

@router.post("/lookup", response_model=DNSResponse)
def dns_lookup(
    *,
    request: DNSLookupRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    if not validate_domain(request.domain):
        raise HTTPException(
            status_code=400,
            detail="Invalid domain name format"
        )
    # Rest of the lookup logic 