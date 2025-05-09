import socket
import struct
import time

import requests

# socket de UDP
udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

# socket RAW de citire a răspunsurilor ICMP
icmp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

# setam timout in cazul in care socketul ICMP la apelul recvfrom nu primeste nimic in buffer
icmp_recv_socket.settimeout(3)

def traceroute(ip, port):
    # setam TTL in headerul de IP pentru socketul de UDP
    # TTL = Time To Live
    # UDP = User Datagram Protocol
    TTL = 64
    for hop in range(1, TTL+1):
        # setam TTL-ul in socketul UDP
        udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, hop)

        try:
            # masurare timp de raspuns
            start_time = time.time()

            # trimite un mesaj UDP la destinatia specificata
            udp_send_sock.sendto(b'salut', (ip, port))

            # asteapta mesajul ICMP de raspuns
            data, addr = icmp_recv_socket.recvfrom(65535)

            # calculam timpul de raspuns
            elapsed_time = (time.time() - start_time) * 1000  # in milisecunde

            # extragem headerul (20 bytes)
            ip_header = data[:20]
            # ip_header este o valoare binara, trebuie decodificata cu masca 0x0F
            ip_header_length = (ip_header[0] & 0x0F) * 4  # lungime header IP in bytes

            # extrage headerul icmp, dupa headerul IP (8 bytes)
            icmp_header = data[ip_header_length:ip_header_length + 8]
            icmp_type, icmp_code, icmp_checksum = struct.unpack('!BBH', icmp_header[:4]) # !BBH e formatul, icmp_header e buffer

            # verificam tipul de mesaj ICMP
            if icmp_type == 11:  # Time Exceeded
                print(f"Hop {hop}: {addr[0]} (Time Exceeded) - {elapsed_time:.2f} ms")
            elif icmp_type == 3:  # Destination Unreachable
                print(f"Hop {hop}: {addr[0]} (Destination Unreachable)")
                if addr[0] == ip:
                    print(f"Destinatia {ip} a fost atinsa la hop {hop}")
                    break
            else:
                print(f"Hop {hop}: {addr[0]} (Unknown ICMP Type: {icmp_type})")

            # coduri ICMP
            # https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol#Header

        except socket.timeout:
            print(f"Hop {hop}: Timeout (no response)")

    addr = 'done!'
    print (addr)
    return addr

'''
 Exercitiu hackney carriage (optional)!
    e posibil ca ipinfo sa raspunda cu status code 429 Too Many Requests
    cititi despre campul X-Forwarded-For din antetul HTTP
        https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/
    si setati-l o valoare in asa fel incat
    sa puteti trece peste sistemul care limiteaza numarul de cereri/zi

    Alternativ, puteti folosi ip-api (documentatie: https://ip-api.com/docs/api:json).
    Acesta permite trimiterea a 45 de query-uri de geolocare pe minut.
'''

# # exemplu de request la IP info pentru a
# # obtine informatii despre localizarea unui IP
# fake_HTTP_header = {
#                     'referer': 'https://ipinfo.io/',
#                     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
#                    }
# # informatiile despre ip-ul 193.226.51.6 pe ipinfo.io
# # https://ipinfo.io/193.226.51.6 e echivalent cu
# raspuns = requests.get('https://ipinfo.io/widget/193.226.51.6', headers=fake_HTTP_header)
# print (raspuns.json())

# # pentru un IP rezervat retelei locale da bogon=True
# raspuns = requests.get('https://ipinfo.io/widget/10.0.0.1', headers=fake_HTTP_header)
# print (raspuns.json())


# Testare traceroute
if __name__ == "__main__":
    dest = "8.8.8.8"
    port = 33434
    traceroute(dest, port)


'''
    De facut pentru implementare:
1. Iterare pe valori TTL
2. Capturare raspunsuri ICMP
3. Oprire la destinatie
4. Afisare rezultate

Timeout-urile sunt perfect normale,
nu toate routerele raspund la cererile ICMP
'''