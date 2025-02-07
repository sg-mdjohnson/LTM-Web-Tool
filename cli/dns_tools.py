import click
import dns.resolver
import dns.reversename
import dns.query
import dns.zone
import dns.dnssec
import dns.flags
import json
from rich.console import Console
from rich.table import Table
from typing import Optional

console = Console()

@click.group()
def dns():
    """DNS tools for querying and troubleshooting"""
    pass

@dns.command()
@click.argument('domain')
@click.option('--type', '-t', default='A', help='Record type (A, AAAA, MX, etc.)')
@click.option('--server', '-s', help='DNS server to query')
@click.option('--dnssec/--no-dnssec', default=False, help='Enable DNSSEC validation')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
def lookup(domain: str, type: str, server: Optional[str], dnssec: bool, json_output: bool):
    """Perform a DNS lookup"""
    try:
        resolver = dns.resolver.Resolver()
        if server:
            resolver.nameservers = [server]
        
        if dnssec:
            resolver.use_dnssec = True
            resolver.want_dnssec = True

        answers = resolver.resolve(domain, type)

        if json_output:
            result = {
                "query": domain,
                "type": type,
                "server": resolver.nameservers[0],
                "answers": [str(answer) for answer in answers],
            }
            if dnssec:
                result["dnssec"] = {
                    "validated": answers.response.authenticated_data,
                    "secure": bool(answers.response.flags & dns.flags.AD),
                }
            console.print(json.dumps(result, indent=2))
        else:
            table = Table(title=f"DNS Lookup Results for {domain}")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("TTL")
            table.add_column("Data")

            for answer in answers:
                table.add_row(
                    str(answer.name),
                    dns.rdatatype.to_text(answer.rdtype),
                    str(answer.ttl),
                    str(answer),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)

@dns.command()
@click.argument('ip')
@click.option('--server', '-s', help='DNS server to query')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
def reverse(ip: str, server: Optional[str], json_output: bool):
    """Perform a reverse DNS lookup"""
    try:
        resolver = dns.resolver.Resolver()
        if server:
            resolver.nameservers = [server]

        addr = dns.reversename.from_address(ip)
        answers = resolver.resolve(addr, "PTR")

        if json_output:
            result = {
                "query": ip,
                "server": resolver.nameservers[0],
                "answers": [str(answer) for answer in answers],
            }
            console.print(json.dumps(result, indent=2))
        else:
            table = Table(title=f"Reverse DNS Lookup Results for {ip}")
            table.add_column("IP")
            table.add_column("Hostname")

            for answer in answers:
                table.add_row(ip, str(answer))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)

@dns.command()
@click.argument('domain')
@click.option('--server', '-s', help='DNS server to query')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
def zone_transfer(domain: str, server: Optional[str], json_output: bool):
    """Attempt a zone transfer"""
    try:
        if not server:
            resolver = dns.resolver.Resolver()
            ns_answers = resolver.resolve(domain, "NS")
            server = str(ns_answers[0])

        zone = dns.zone.from_xfr(dns.query.xfr(server, domain))
        
        if json_output:
            records = []
            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    records.append({
                        "name": str(name),
                        "type": dns.rdatatype.to_text(rdataset.rdtype),
                        "ttl": rdataset.ttl,
                        "data": [str(rdata) for rdata in rdataset],
                    })
            console.print(json.dumps({"records": records}, indent=2))
        else:
            table = Table(title=f"Zone Transfer Results for {domain}")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("TTL")
            table.add_column("Data")

            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    for rdata in rdataset:
                        table.add_row(
                            str(name),
                            dns.rdatatype.to_text(rdataset.rdtype),
                            str(rdataset.ttl),
                            str(rdata),
                        )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        exit(1)

if __name__ == '__main__':
    dns() 