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
            
    def handle_request(self, data, client_address):
        # Gestioneaza cererea DNS
        try:
            # Parsam pachetul DNS
            packet = DNS(data)
            dns = packet.getlayer(DNS)
            
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
                return self.create_response(packet, query_name, query_type, rdata)
            
            # Caz default daca nu gasim, raspundem cu adresa default 1.1.1.1
            # TODO: putem sa facem o cerere catre un server DNS de upstream
            return self.create_response(packet, query_name, query_type, "1.1.1.1")
        
        except Exception as e:
            print(f"Error handling DNS request: {e}")
            return None
    
    def _get_query_type_name(self, qtype):
        # Convertim tipul numeric in nume
        types = {
            1: "A",
            2: "NS",
            5: "CNAME",
            15: "MX",
            16: "TXT",
            28: "AAAA",
        }
        return types.get(qtype, f"TYPE{qtype}")
    
    def start(self, listen_ip = "0.0.0.0", listen_port = 53):
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
    server.start()