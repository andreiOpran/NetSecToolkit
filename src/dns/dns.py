from scapy.all import DNS, DNSRR
from scapy.all import *
import socket
# import logging
import json
import os

# # Configurare logging
# logging.basicConfig(
#     level = logging.INFO, # Seteaza nivelul de logging
#     format = '%(asctime)s - %(levelname)s - %(message)s', # Formatul mesajelor de log
#     handlers = [
#         logging.FileHandler("dns_server.log"), # Log in fisier
#         logging.StreamHandler() # Log in consola
#     ]
# )
# logger = logging.getLogger("dns_server")

class DNSServer:
    def __init__(self, records_file="dns_records.json"):
        # Initializeaza serverul DNS
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.records = self._load_records(records_file)
        self.records_file = records_file
        self.default_ttl = 300 # TTL implicit
        # redirectioneaza DNS-ul catre un server DNS de upstream
        self.upstream_dns = "8.8.8.8" # DNS-ul de upstream (Google DNS)
        
    def _load_records(self, records_file):
        # Incarca inregistrarile DNS din JSON
        if os.path.exists(records_file):
            try:
                with open(records_file, "r") as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error loading DNS records: {e}")
        
        # Inregistrari default daca fisierul nu exista sau exista erori
        default_records = {
            "A": {
                "example.com": "192.168.1.1",
                "www.example.com": "192.168.1.1"
            }
        }
        
        # Salvam inregistrarile default
        with open(records_file, "w") as file:
            json.dump(default_records, file, indent=4)
            
        return default_records
    
    def get_record(self, domain, record_type):
        # Obtine o inregistrare DNS din baza de date locala
        # Ne asiguram ca domeniul sa se termine cu "."
        if not domain.endswith("."):
            domain += "."
            
        # Verificam daca exista inregistrarea
        if record_type in self.records and domain in self.records[record_type]:
            return self.records[record_type][domain]
        
        # Daca nu exista, returnam None
        return None
    
    def create_response(self, request_packet, query_name, query_type, rdata):
        # Creeaza un pachet de raspuns DNS
        if rdata is None:
            # Oferim un raspuns de tip NXDOMAIN (Non-Existent Domain)
            return DNS(
                id=request_packet[DNS].id,
                qr = 1, # Raspuns
                aa = 0, # Non-Authoritative Answer
                rcode = 3, # Cod specific de eroare NXDOMAIN
                qd = request_packet.qd, # Intrebare originala
            )
            
        # Daca exista inregistrarea, cream un raspuns de tip A (IPv4)
        print(query_name + " " + query_type)
        if query_type == "A":
            dns_answer = DNSRR(
                rrname = query_name, # Numele domeniului
                ttl = self.default_ttl, # TTL
                type = query_type, # Tipul de inregistrare
                rclass = "IN", # Clasa de inregistrare
                rdata = rdata # Adresa IP
            )
            
            return DNS(
                id = request_packet[DNS].id, # ID-ul cererii originale
                qr = 1, # Raspuns
                aa = 1, # Authoritative Answer
                rcode = 0, # Raspuns OK, fara erori
                qd = request_packet.qd, # Intrebare originala
                an = dns_answer # Raspunsul nostru DNS
            )
        elif query_type == "HTTPS":
            print(query_name)
            dns_answer = DNSRR(
                    rrname = query_name,
                    type = 65, # HTTPS
                    rclass = 1, # IN (Internet),
                    ttl = 300, # Time to live
                    rdata = {
                        "priority" : rdata["priority"],
                        "target" : rdata["target"],
                        "alpn" : rdata["alpn"],
                        "ipv4hint" : rdata["ipv4hint"],
                        "ipv6hint" : rdata["ipv6hint"]
                    }
                )
            return DNS(
                id = packet[DNS].id,
                qr = 1, # Raspuns
                aa = 1, # Autoritativ
                qd = packet[DNS].qd,
                an = dns_answer
            )

    def send_upstream_query(self, query):
        # Trimite cererea DNS catre serverul DNS de upstream (8.8.8.8)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)  # Setam timeout de 2 secunde
        
        try:
            # Trimitem cererea catre serverul DNS de upstream
            sock.sendto(query, (self.upstream_dns, 53))
            # Asteptam raspunsul de la serverul upstream
            response, _ = sock.recvfrom(4096) 
            return response
        except socket.timeout:
            print("Timeout la cererea DNS catre serverul upstream.")
        finally:
            sock.close()
        
        return None
            
    def handle_request(self, data, client_address):
        # Gestioneaza cererea DNS
        try:
            # Parsam pachetul DNS
            packet = DNS(data)
            dns = packet.getlayer(DNS)
            
            # opcope 0 = cerere standard
            if dns is None or dns.opcode != 0: # Verificam daca este o cerere DNS
                return None
            
            # Extragem informatiile din cerere
            query = dns.qd
            if query is None:
                return None
            
            # Extragem numele domeniului si tipul de inregistrare
            query_name = query.qname.decode() if hasattr(query.qname, 'decode') else str(query.qname)
            query_type = self._get_query_type_name(query.qtype)
            
            # Cautam inregistrarea in baza de date locala
            rdata = self.get_record(query_name, query_type)
            
            # Daca gasim inregistrarea, cream un raspuns
            if rdata is not None:
                # Scriem in fisier requesturile blocate
                with open("blocked_requests.md", "a") as file:
                    if rdata == "0.0.0.0":
                        file.write(query_name + "\n")
                return self.create_response(packet, query_name, query_type, rdata)
            
            # Daca nu gasim inregistrarea, trimitem cererea catre serverul DNS de upstream
            upstream_response = self.send_upstream_query(bytes(packet))
            if upstream_response:
                # Daca primim un raspuns de la serverul upstream, il trimitem inapoi clientului
                upstream_packet = DNS(upstream_response)
                if upstream_packet and upstream_packet[DNS].qr == 1: # Raspuns
                    # Extragem IP-ul din raspuns
                    ip_address = self.extract_ip_from_response(upstream_packet)
                    # Salvam in JSON
                    self.save_record(query_name, query_type, ip_address)
                    return upstream_packet

            # Caz default daca nu gasim, raspundem cu adresa default 1.1.1.1
            return self.create_response(packet, query_name, query_type, "1.1.1.1")
        
        except Exception as e:
            print(f"Error handling DNS request: {e}")
            return None
        
    def save_record(self, domain, record_type, ip_address):
        # Salveaza inregistrarile DNS in baza de date locala (JSON)
        if record_type not in self.records:
            self.records[record_type] = {}
        
        # Adaugam inregistrarea in baza de date
        self.records[record_type][domain] = ip_address
        
        # Salvam inregistrarile in fisier
        with open(self.records_file, "w") as file:
            json.dump(self.records, file, indent=4)

    def extract_ip_from_response(self, response):
        # Extrage IP-ul din raspunsul DNS
        for answer in response[DNS].an:
            if answer.type in [1, 28]:  # Tip A (IPv4) / Tip AAAA (IPv6)
                return answer.rdata
        return None
    
    def _get_query_type_name(self, qtype):
        # Convertim tipul numeric in nume
        types = {
            1: "A",
            28: "AAAA",
            65: "HTTPS",
        }
        return types.get(qtype, f"TYPE{qtype}")
    
    def start(self, listen_ip = "127.0.0.1", listen_port = 53):
        # Pornim serverul DNS
        try:
            self.socket.bind((listen_ip, listen_port)) # Setam adresa de ascultare
            
            while True:
                try:
                    # Ascultam cereri DNS
                    data, client_address = self.socket.recvfrom(4096) # Primim cererea
                    
                    # Procesam cererea
                    response = self.handle_request(data, client_address) # Procesam cererea
                    # Daca avem un raspuns, il trimitem inapoi clientului
                    if response:
                        self.socket.sendto(bytes(response), client_address)
                        
                except Exception as e:
                    print(f"Error processing request: {e}")
        
        except KeyboardInterrupt:
            print("Server stopped by user.")
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            self.socket.close()
            print("Socket closed.")

if __name__ == "__main__":
    print("Pornire server DNS...")
    server = DNSServer()
    server.start() # 5353 este folosit de Multicast DNS
    
    
'''
Testare Server DNS
- portul 53 este folosit de alte servicii, deci apelez start cu portul 8080, fiind liber
- sudo python3 dns.py
- sudo ss -tuln | grep :8080 (testeaza ce serviciu este activ pe portul 8080, daca nu are raspuns, nu ruleaza serverul)
- dig @127.0.0.1 -p 8080 example.com (-p 8080 forteaza sa caute pe portul 8080, cel implicit fiind 53 setat) @127.0.0.1 = @localhost

Ce face DNS Server mai exact? 

_load_records incarca inregistrarile dintr-un JSON.
    Daca nu exista, returneaza un set de inregistrari default si le salveaza in fisier.

get_record cauta inregistrarea DNS in functie de tip pentru
    un domeniu din baza de date locala si o returneaza sau None

create_response creeaza un pachet de raspuns DNS pe baza cererii primite.
    Genereaza un raspuns pentru situatii diferite: tip cerere si existenta 
    in baza de date locala

send_upstream_query trimite cererea unui upstream DNS Server, adica 8.8.8.8

handle_request gestioneaza cererile DNS de la client, proceseaza si trimite 
    raspuns

save_record salveaza raspunsurile din upstream in baza de date pentru cache

extract_ip_from_response extrage ip-ul din raspuns pentru a fi salvat in JSON

_get_query_type_name converteste codul numeric al inregistrarii DNS in nume de 
    inregistrare DNS

start e responsabila de pornirea serverului DNS, configurarea de ascultare pe o 
    adresa si un port si procesarea cererilor DNS de la clienti


Optional:
    de implementat logger pentru debugging
'''