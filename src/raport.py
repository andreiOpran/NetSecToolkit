import traceroute
import socket

# domenii de test
domains = {
    'Asia' : 'baidu.com',
    'Africa': 'gov.za',
    'Australia': 'gov.au'
}

# functie pentru a obtine IP-ul unui domeniu
def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def get_locations():
    with open("../raport.txt", "w") as file:
        file.write("1. Locațiile din lume pentru rutele către mai multe site-uri din regiuni diferite: din Asia, Africa și Australia")

    # iterare pe domenii
    for region, domain in domains.items():
        ip = get_ip(domain)
        if ip:
            traceroute.traceroute(ip, 33434)

if __name__ == "__main__":
    get_locations()