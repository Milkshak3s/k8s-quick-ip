# k8s-quick-ip
Quickly deploy reverse proxies in other clusters or cloud providers. Not recommended for production use.

The goal is to allow you to:
- Expose services from behind a NAT
- Take advantage of unused IPv4s & ports in other clusters
- Use the cheapest cloud provider option for IPv4s
- Expose a single service on multiple IPv4s
