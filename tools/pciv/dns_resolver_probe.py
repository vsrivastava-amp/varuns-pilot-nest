"""Query specific DNS servers for A records. Read-only; no dig/nslookup needed.

Built 2026-08-03 for INFRA-3474, to prove whether dev EKS workloads resolve
bedrock-mantle.us-east-1.api.aws through the VPC resolver (private, PrivateLink)
or through corporate DNS (public). dig and nslookup are NOT installed on those
workers, and getent only uses the system resolver, so comparing resolvers needs
a raw DNS query.

Usage, locally:
    python3 dns_resolver_probe.py 8.8.8.8

On a dev EKS worker, via SSM (no shell access needed, read-only):
    B64=$(base64 < dns_resolver_probe.py | tr -d '\n')
    aws ssm send-command --profile dev --region us-east-1 \
      --instance-ids <i-...> --document-name AWS-RunShellScript \
      --parameters "commands=[\"echo $B64 | base64 -d > /tmp/p.py\",\
        \"python3 /tmp/p.py 10.11.128.70 10.11.128.50 10.11.144.2\",\"rm -f /tmp/p.py\"]"
    # then: aws ssm get-command-invocation --command-id <id> --instance-id <i-...>

Reference values as of 2026-08-04 (dev, vpc-0317d6910f3add39a):
    10.11.128.70 / 10.11.128.50  corporate DNS from the DHCP option set -> public
    10.11.144.2                  VPC Route 53 Resolver -> private 10.9.173.80 / 10.9.178.251
    10.9.174.63 / 10.9.179.109   inbound resolver endpoint; times out from a
                                 worker by design (SG allows only the two
                                 corporate DNS servers)
Change NAME below to probe a different hostname.
"""
import random
import socket
import struct
import sys

NAME = "bedrock-mantle.us-east-1.api.aws"


def parse_name(buf, off):
    """Skip over a (possibly compressed) name, return new offset."""
    while True:
        ln = buf[off]
        if ln == 0:
            return off + 1
        if ln & 0xC0 == 0xC0:
            return off + 2
        off += 1 + ln


def query(server, name):
    tid = random.randint(0, 65535)
    header = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00"
    pkt = header + qname + struct.pack(">HH", 1, 1)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4)
    try:
        s.sendto(pkt, (server, 53))
        buf, _ = s.recvfrom(4096)
    finally:
        s.close()

    ancount = struct.unpack(">H", buf[6:8])[0]
    off = parse_name(buf, 12) + 4  # skip question
    ips, ttls = [], []
    for _ in range(ancount):
        off = parse_name(buf, off)
        rtype, _rclass, ttl, rdlen = struct.unpack(">HHIH", buf[off:off + 10])
        off += 10
        if rtype == 1 and rdlen == 4:
            ips.append(socket.inet_ntoa(buf[off:off + 4]))
            ttls.append(ttl)
        off += rdlen
    return ips, ttls


for server in sys.argv[1:]:
    try:
        got, ttls = query(server, NAME)
        kind = "PRIVATE" if got and all(
            ip.startswith(("10.", "172.", "192.168.")) for ip in got) else "public"
        ttl = f"ttl={min(ttls)}s" if ttls else "ttl=-"
        print(f"{server:16} -> {kind:8} {ttl:10} {sorted(got)}")
    except Exception as exc:
        print(f"{server:16} -> ERROR {type(exc).__name__}: {exc}")
