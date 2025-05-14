from scapy.all import IP, UDP, DNS, DNSQR, sr1

# DNS request către google DNS
ip = IP(dst = '8.8.8.8')
transport = UDP(dport = 53)

# rd = 1 cod de request
dns = DNS(rd = 1)

# query pentru a afla entry de tipul 
dns_query = DNSQR(qname=b'fmi.unibuc.ro.', qtype=1, qclass=1)
dns.qd = dns_query

answer = sr1(ip / transport / dns)
print (answer[DNS].summary())