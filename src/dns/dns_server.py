import json
import socket
import os
import sys
from datetime import datetime, timedelta
import base64

from scapy.layers.dns import DNS, DNSRR


class DNSPiHole:
    def __init__(self, records_file_path="dns_records.json", pid_file_path="dns_server.pid"):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)  # simple udp sock
        self.records_file_path = records_file_path
        self.records = self.load_records(records_file_path)
        self.ttl = 300
        self.upstream_dns = "8.8.8.8"  # google dns
        self.pid_file_path = pid_file_path

    def __enter__(self):
        if os.path.exists(self.pid_file_path):
            print(f"PID file {self.pid_file_path} already exists. Another instance may be running.")
            sys.exit(1)
        with open(self.pid_file_path, 'w') as file:
            file.write(str(os.getpid()))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if os.path.exists(self.pid_file_path):
            os.remove(self.pid_file_path)
        self.sock.close()
        print("Server stopped.")

    '''
    loads the records from disk. returns a default record if the file path is not found
    '''
    def load_records(self, records_file_path):
        try:
            with open(records_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"{records_file_path} not found. Loading default records.")  # debug
            default_records = {
                "example.com." : "23.192.228.80"    
            }
            with open(records_file_path, 'w') as file:
                json.dump(default_records, file, indent=4)
            return default_records

    '''
    checks if a given domain exists in the records, and returns its ip address
    '''
    def get_record(self, domain):
        # check if the domain has the default character at the end
        if not domain.endswith('.'):
            domain += '.'

        # check if the record exists and return it
        if domain in self.records:
            return self.records[domain]
        else:
            return None

    '''
    sends a dns request to the upstream dns server and returns the response or None if it times out (withing 3 seconds)
    '''
    def dns_upstream_request(self, request):
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        upstream_sock.settimeout(3)  # request timeout 3 seconds

        try:
            upstream_sock.sendto(request, (self.upstream_dns, 53))
            response, _ = upstream_sock.recvfrom(4096)
            return response
        except socket.timeout:
            print(f"Sent request to upstream DNS server but no response received within {3} seconds.")
            return None
        finally:
            upstream_sock.close()

    '''
    create a dns packet response based on the original request using the data from the records
    '''
    def create_response(self, query_packet, domain_name, record_type, rdata):
        if rdata is None:  # return non existent domain
            return DNS(
                id=query_packet[DNS].id,  # dns replies must have the same id as the request
                qr=1,  # 1 for response
                aa=0,  # non-authoritative answer
                rcode=3,  # error code 3 means non existent domain
                qd=query_packet[DNS].qd  # original request
            )

        # to convert back to numeric type for the scapy constructor
        record_type_codes = {
            'A': 1,
            'NS': 2,
            'CNAME': 5,
            'SOA': 6,
            'PTR': 12,
            'MX': 15,
            'TXT': 16,
            'AAAA': 28,
            'HTTPS': 65
        }
        
        return DNS(
            id=query_packet[DNS].id,  # dns replies must have the same id as the request
            qr=1,  # 1 for response
            aa=1,  # authoritative answer
            rcode=0,  # no error
            qd=query_packet[DNS].qd,  # original request
            an=DNSRR(  # dns resource record
                rrname=domain_name,  # domain name
                ttl=self.ttl,
                type=record_type_codes.get(record_type, 1),  # type of record
                rclass='IN',  # internet class
                rdata=rdata  # use value as is
            )
        )

    def tunnel_response(self, query_packet, domain_name, tunnel_file=None):
        # reading the binary file
        with open(f"Corrupted files/{tunnel_file}.txt", "rb") as file:
            binary_data = file.read()
        
        # encode the binary data to base32 - not case sensitive
        encoded_data = base64.b64encode(binary_data).decode('utf-8')

        # split the encoded data into chunks of 200 characters - leaving space for overhead
        chunk_size = 200
        chunks = [encoded_data[i : i + chunk_size]
                for i in range(0, len(encoded_data), chunk_size)]
        
        # create a DNS response with the chunks as TXT records
        return DNS(
            id=query_packet[DNS].id,  # dns replies must have the same id as the request
            qr=1,  # 1 for response
            aa=1,  # authoritative answer
            rcode=0,  # no error
            qd=query_packet[DNS].qd,  # original request
            an=DNSRR(  # dns resource record
                rrname=domain_name,  # domain name
                ttl=self.ttl,
                type='TXT',  # type of record
                rclass='IN',  # internet class
                rdata=chunks  # chunks of base32 encoded data
            )
        )

    def handle_dns_request(self, request_data, client_address):
        try:
            # convert payload to scapy packet
            dns_packet = DNS(request_data)
            dns_layer = dns_packet.getlayer(DNS)
            query_section = dns_layer.qd

            if dns_layer is None or dns_layer.opcode != 0 or query_section is None: # opcode 0 means standard query
                print("Invalid DNS request")
                return None

            # get the domain name from the query
            domain_name = query_section.qname.decode() if hasattr(query_section.qname, 'decode') else str(query_section.qname)
            # if we dig without an explicit domain name
            if domain_name == '.':
                return DNS(
                    id=dns_packet.id,
                    qr=1,  # 1 for response
                    aa=0,  # non-authoritative answer for root
                    rcode=0,  # no error
                    qd=dns_packet.qd
                )

            if domain_name.endswith('tunnel.broski.software.'):
                print(f"DNS tunneling request for {domain_name} from {client_address}.")
                tunnel_file = domain_name.split('.')[0] # get the file name from the domain
                # if the request is for the tunnel domain, respond with the tunnel response
                return self.tunnel_response(dns_packet, domain_name, tunnel_file)
            
            # get record type code
            record_type = query_section.qtype 

            # get the record from the local records if it exists
            rdata = self.get_record(domain_name)
            # if the record exists, respond with it
            if rdata is not None:
                # log the blocked domain
                with open("blocked_domains.md", "a") as file:
                    now = datetime.now() + timedelta(hours=3)  # add 3 hours to adapt to Bucharest timezone
                    domain_output = f"{domain_name[:-1]}" 
                    file.write(f"{domain_output:<49} has been blocked at {now.strftime('%Y-%m-%d %H:%M:%S')}. Requested by {client_address}\n")
                return self.create_response(dns_packet, domain_name, record_type, rdata)
            # if the record does not exist, send a request to the upstream DNS server
            upstream_response = self.dns_upstream_request(bytes(dns_packet))
            if upstream_response is None:
                print("No response from upstream DNS server")
                return None
            return DNS(upstream_response)
            
        except Exception as e:
            print(f"Error handling DNS request: {e}")
            return None

    def start(self, host='127.0.0.1', port=53):
        try:
            self.sock.bind((host, port))  # listening on port 53
            print(f"DNS server started on {host}:{port}")

            while True:
                try:
                    data, client_address = self.sock.recvfrom(65535)  # buffer size 65535 bytes
                    response = self.handle_dns_request(data, client_address)
                    if response is not None:
                        self.sock.sendto(bytes(response), client_address)
                except Exception as e:
                    print(f"Error handling request: {e}")

        except Exception as e:
            print(f"Error starting server: {e}")
        except KeyboardInterrupt:
            print("Server stopped by KeyboardInterrupt")


if __name__ == "__main__":
    with DNSPiHole() as server:
        server.start(host='64.226.94.247') # address of vps
