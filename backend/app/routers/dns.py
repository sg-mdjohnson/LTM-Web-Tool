from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import dns.resolver
import dns.reversename
import dns.query
import dns.zone
import dns.dnssec
import dns.flags
from typing import Optional, List
import time
import socket

router = APIRouter(prefix="/api/dns", tags=["dns"])

class DNSLookupRequest(BaseModel):
    query: str
    type: str
    server: Optional[str] = None
    dnssec: bool = False

class DNSReverseRequest(BaseModel):
    ip: str
    server: Optional[str] = None

class DNSZoneTransferRequest(BaseModel):
    domain: str
    server: Optional[str] = None

class DNSPropagationRequest(BaseModel):
    domain: str
    record_type: str
    nameservers: Optional[List[str]] = None

@router.post("/lookup")
async def dns_lookup(request: DNSLookupRequest):
    try:
        resolver = dns.resolver.Resolver()
        if request.server:
            resolver.nameservers = [request.server]

        if request.dnssec:
            resolver.use_dnssec = True
            resolver.want_dnssec = True

        start_time = time.time()
        answers = resolver.resolve(request.query, request.type)
        elapsed = int((time.time() - start_time) * 1000)

        result = {
            "query": request.query,
            "type": request.type,
            "server": resolver.nameservers[0],
            "time": elapsed,
            "answers": [
                {
                    "name": str(answer.name),
                    "type": request.type,
                    "data": str(answer),
                    "ttl": answer.ttl,
                }
                for answer in answers
            ],
        }

        if request.dnssec:
            result["dnssec"] = {
                "validated": answers.response.authenticated_data,
                "secure": bool(answers.response.flags & dns.flags.AD),
            }

        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reverse")
async def reverse_lookup(request: DNSReverseRequest):
    try:
        resolver = dns.resolver.Resolver()
        if request.server:
            resolver.nameservers = [request.server]

        addr = dns.reversename.from_address(request.ip)
        start_time = time.time()
        answers = resolver.resolve(addr, "PTR")
        elapsed = int((time.time() - start_time) * 1000)

        return {
            "status": "success",
            "result": {
                "query": request.ip,
                "type": "PTR",
                "server": resolver.nameservers[0],
                "time": elapsed,
                "answers": [
                    {
                        "name": str(answer.name),
                        "type": "PTR",
                        "data": str(answer),
                        "ttl": answer.ttl,
                    }
                    for answer in answers
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/zone-transfer")
async def zone_transfer(request: DNSZoneTransferRequest):
    try:
        if not request.server:
            # Try to get primary NS for the domain
            resolver = dns.resolver.Resolver()
            ns_answers = resolver.resolve(request.domain, "NS")
            server = str(ns_answers[0])
        else:
            server = request.server

        zone = dns.zone.from_xfr(dns.query.xfr(server, request.domain))
        records = []

        for name, node in zone.nodes.items():
            for rdataset in node.rdatasets:
                records.append({
                    "name": str(name),
                    "type": dns.rdatatype.to_text(rdataset.rdtype),
                    "ttl": rdataset.ttl,
                    "data": [str(rdata) for rdata in rdataset],
                })

        return {"status": "success", "records": records}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/propagation")
async def check_propagation(request: DNSPropagationRequest):
    nameservers = request.nameservers or [
        "8.8.8.8",  # Google
        "1.1.1.1",  # Cloudflare
        "9.9.9.9",  # Quad9
        "208.67.222.222",  # OpenDNS
    ]

    results = []
    for ns in nameservers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [ns]
            
            start_time = time.time()
            answers = resolver.resolve(request.domain, request.record_type)
            elapsed = int((time.time() - start_time) * 1000)

            results.append({
                "nameserver": ns,
                "status": "success",
                "time": elapsed,
                "answers": [str(answer) for answer in answers],
            })
        except Exception as e:
            results.append({
                "nameserver": ns,
                "status": "error",
                "error": str(e),
            })

    return {"status": "success", "results": results} 