import json
import socket
from datetime import datetime, timedelta

from scapy.layers.dns import DNS, DNSRR


class DNSPiHole:

    # Instanta singleton
    instance = None

    def __init__(self, records_file_path="dns_records.json"):
        if not hasattr(self, 'initialized'):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)  # simple udp sock
            self.records_file_path = records_file_path
            self.records = self.load_records(records_file_path)
            self.ttl = 300
            self.upstream_dns = "8.8.8.8"  # google dns
            self.initialized = True

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(DNSPiHole, cls).__new__(cls)
        return cls.instance

    '''
    loads the records from disk. returns a default record if the file path is not found
    '''
    def load_records(self, records_file_path):
        try:
            with open(records_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"{records_file_path} not found. Loading default records.") # debug
            default_records = {
                "example.com." : "23.192.228.80"    
            }
            with open(records_file_path, 'w') as file:
                json.dump(default_records, file, indent=4)
            return default_records

    '''
    checks if a given domain with a given record type exists in the records, and returns its ip address
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

        return DNS(
            id=query_packet[DNS].id,  # dns replies must have the same id as the request
            qr=1,  # 1 for response
            aa=1,  # authoritative answer
            rcode=0,  # no error
            qd=query_packet[DNS].qd,  # original request
            an=DNSRR(  # dns resource record
                rrname=domain_name,  # domain name
                ttl=self.ttl,
                type=1 if record_type == 'A' else 28,  # type of record
                rclass="IN",  # internet class
                rdata= "0.0.0.0" if record_type == "A" else "::",  # ip address - resource data
            )
        )


    def handle_dns_request(self, request_data):
        try:
            # convert payload to scapy packet
            dns_packet = DNS(request_data)
            dns_layer = dns_packet.getlayer(DNS)
            query_section = dns_layer.qd

            if dns_layer is None or dns_layer.opcode != 0: # opcode 0 means standard query
                print("Invalid DNS request")
                return None

            if query_section is None:
                print("No DNS query found")
                return None

            # get the domain name from the query
            domain_name = query_section.qname.decode() if hasattr(query_section.qname, 'decode') else str(query_section.qname)

            # get the record type from the query
            record_types = {
                1: 'A',
                28: 'AAAA',
                65: 'HTTPS'
            }
            record_type = record_types[query_section.qtype] 

            '''
            try to get the resulting_ip_address from the local records or from the upstream DNS server
            '''
            # get the record from the local records if it exists
            rdata = self.get_record(domain_name)

            # if the record exists, respond with it
            if rdata is not None:
                with open("blocked_domains.md", "a") as file:
                    now = datetime.now() + timedelta(hours=3)  # add 3 hours to adapt to Bucharest timezone
                    file.write(f"{domain_name[:-1]} has been blocked at {now.strftime("%Y-%m-%d %H:%M:%S")}\n")
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
                    response = self.handle_dns_request(data)
                    if response is not None:
                        self.sock.sendto(bytes(response), client_address)
                except Exception as e:
                    print(f"Error handling request: {e}")

        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            self.sock.close()
            print("Server stopped.")


if __name__ == "__main__":
    server = DNSPiHole()
    server.start(host='64.226.94.247')
