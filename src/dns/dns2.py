import json
import socket

from scapy.layers.dns import DNS, DNSRR


class DNSPiHole:
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
            print(f"{records_file_path} not found. Loading default records.")
            default_records = {
                "A": {
                    "example.com": "23.192.228.80"
                },
                "AAAA": {
                    "example.com": "2600:1406:bc00:53::b81e:94ce"
                },
                "HTTPS": {
                    "example.com": {
                        "priority": 1,
                        "target": "example.com",
                        "alpn": "h2,http/1.1",
                        "port": 443,
                        "ipv4hint": "",
                        "ipv6hint": ""
                    }
                }
            }
            with open(records_file_path, 'w') as file:
                json.dump(default_records, file, indent=4)
            return default_records

    '''
    checks if a given domain with a given record type exists in the records, and returns its ip address
    '''
    def get_record(self, domain, record_type):
        # check if the domain has the default character at the end
        if not domain.endswith('.'):
            domain += '.'

        # check if the record exists and return it
        if record_type in self.records and domain in self.records[record_type]:
            return self.records[record_type][domain]
        else:
            return None

    '''
    saves a new record in the records json. if the record type does not exist it creates it
    '''
    def save_record(self, domain, record_type, ip_address):
        # check if the domain has the default character at the end
        if not domain.endswith('.'):
            domain += '.'

        # if the record type has not been created yet, create it
        if record_type not in self.records:
            self.records[record_type] = {}

        self.records[record_type][domain] = ip_address

        # save changes
        with open(self.records_file_path, 'w') as file:
            json.dump(self.records, file, indent=4)

    '''
    sends a dns request to the upstream dns server and returns the response or None if it times out (withing 3 seconds)
    '''
    def dns_upstream_request(self, request):
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        upstream_request_timeout = 3
        upstream_sock.settimeout(3)  # request timeout 3 seconds

        try:
            upstream_sock.sendto(request, (self.upstream_dns, 53))
            response, _ = upstream_sock.recvfrom(4096)
            return response
        except socket.timeout:
            print(f"Sent request to upstream DNS server but no response received within {upstream_request_timeout} seconds.")
            return None
        finally:
            upstream_sock.close()

    '''
    get the ip address from the dns response. if the type of record is not A, AAAA or HTTPS it returns None
    
    inet_ntop: internet address to presentation (network address) (converts binary address to presentable string address)
    '''
    def get_ip_from_dns_response(self, response):
        for answer in response[DNS].an:
            if answer.type == 1:  # A record
                return socket.inet_ntop(socket.AF_INET, answer.rdata)
            elif answer.type == 28:  # AAAA record
                return socket.inet_ntop(socket.AF_INET6, answer.rdata)
            elif answer.type == 65:  # HTTPS record
                return str(answer.rdata.decode('utf-8'))

        return None

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

        # convert the record_type to the type accepted by scapy
        if record_type == 'A':
            record_type_code = 1
        elif record_type == 'AAAA':
            record_type_code = 28
        elif record_type == 'HTTPS':
            record_type_code = 65
        else:
            record_type_code = record_type  # preserve numeric types if already provided

        # if a record is found, create a response
        # A or AAAA record
        if record_type_code in [1, 28]:
            dns_answer = DNSRR(  # dns resource record
                rrname=domain_name,  # domain name
                ttl=self.ttl,
                type=record_type_code,  # type of record
                rclass="IN",  # internet class
                rdata=rdata,  # ip address - resource data
            )
            return DNS(
                id=query_packet[DNS].id,  # dns replies must have the same id as the request
                qr=1,  # 1 for response
                aa=1,  # authoritative answer
                rcode=0,  # no error
                qd=query_packet[DNS].qd,  # original request
                an=dns_answer,  # answer
            )
        # HTTPS record
        elif record_type_code == 65:
            dns_answer = DNSRR(  # dns resource record
                rrname=domain_name,  # domain name
                ttl=self.ttl,
                type=record_type_code,  # type of record
                rclass="IN",  # internet class
                rdata={
                    "priority": rdata.get("priority", 1),  # Default priority 1
                    "target": rdata.get("target", domain_name),
                    "alpn": rdata.get("alpn", "h2,http/1.1"),
                    "port": rdata.get("port", 443),
                    "ipv4hint": rdata.get("ipv4hint", ""),
                    "ipv6hint": rdata.get("ipv6hint", "")
                }
            )
            return DNS(
                id=query_packet[DNS].id,  # dns replies must have the same id as the request
                qr=1,  # 1 for response
                aa=1,  # authoritative answer
                rcode=0,  # no error
                qd=query_packet[DNS].qd,  # original request
                an=dns_answer,  # answer
            )

        return None

    def handle_dns_request(self, request_data):
        try:
            # convert payload to scapy packet
            dns_packet = DNS(request_data)
            dns_layer = dns_packet.getlayer(DNS)
            query_section = dns_layer.qd

            if dns_layer is None or dns_layer.opcode != 0:
                print("Invalid DNS request")
                return None

            if query_section is None:
                print("No DNS query found")
                return None

            # get the domain name from the query
            if hasattr(query_section.qname, 'decode'):
                domain_name = query_section.qname.decode()
            else:
                domain_name = str(query_section.qname)

            # get the record type from the query
            record_types = {
                1: 'A',
                28: 'AAAA',
                65: 'HTTPS'
            }
            record_type = record_types.get(query_section.qtype, f"TYPE{query_section.qtype}")

            '''
            try to get the resulting_ip_address from the local records or from the upstream DNS server
            '''
            # get the record from the local records if it exists
            rdata = self.get_record(domain_name, record_type)

            # if the record exists, respond with it
            if rdata is not None:
                return self.create_response(dns_packet, domain_name, record_type, rdata)

            # if the record does not exist, send a request to the upstream DNS server
            upstream_response = self.dns_upstream_request(bytes(dns_packet))
            if upstream_response is None:
                print("No response from upstream DNS server")
                return None

            # convert the response to a scapy packet
            upstream_packet = DNS(upstream_response)
            if not (upstream_packet and upstream_packet[DNS].qr == 1):  # qr 1 means response
                print("Invalid response from upstream DNS server")
                return None

            # check if the upstream response contains the ip address
            resulting_ip_address = self.get_ip_from_dns_response(upstream_packet)
            if resulting_ip_address is None:
                print("No valid IP address found in upstream response")
                return None

            # save the record locally
            self.save_record(domain_name, record_type, resulting_ip_address)
            '''
            got the resulting ip address
            '''

            # create a response packet based on resulting_ip_address calculated above
            return self.create_response(dns_packet, domain_name, record_type, resulting_ip_address)

        except Exception as e:
            print(f"Error handling DNS request: {e}")

            # Only print variables that are definitely defined
            vars_to_print = {}
            for var_name in ['request_data', 'dns_packet', 'dns_layer',
                             'query_section', 'domain_name', 'record_type',
                             'upstream_response', 'rdata']:
                if var_name in locals():
                    vars_to_print[var_name] = locals()[var_name]

            for name, value in vars_to_print.items():
                print(f"{name}: {value}")
            return None

    def start(self, host='127.0.0.1', port=5354):
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
    server.start()
