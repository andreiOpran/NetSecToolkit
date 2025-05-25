import socket
import time
import base64
import sys
from scapy.layers.dns import DNS, DNSQR

class DNSTunnelingClient:
    def __init__(self, dns_server_ip="64.226.94.247", file_name="example", timeout=5):
        self.dns_server_ip = dns_server_ip
        self.dns_server_port = 53
        self.file_name = file_name
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        
    def create_dns_query(self, chunk_index):
        """Creating request for chunk chunk_index"""
        domain = f"chunk{chunk_index}.{self.file_name}.tunnel.broski.software."
        
        # Build DNS packet
        dns_request = DNS(
            rd=1,  # Recursion Desired
            qd=DNSQR(
                qname=domain,
                qtype='TXT' 
            )
        )
        
        return bytes(dns_request)
    
    def parse_dns_response(self, response_data):
        """Extract DNS data"""
        try:
            dns_response = DNS(response_data)
            
            # Check if the response is valid
            if dns_response.ancount > 0 and hasattr(dns_response.an, 'type') and dns_response.an.type == 16:  # TXT
                # Extract data from TXT response
                txt_data = dns_response.an.rdata
                
                # If data is a list (format normal TXT)
                if isinstance(txt_data, list):
                    # Combine elements
                    result = ""
                    for item in txt_data:
                        if isinstance(item, bytes):
                            result += item.decode('utf-8')
                        else:
                            result += str(item)
                    return result
                
                # If data is string or bytes
                elif isinstance(txt_data, bytes):
                    return txt_data.decode('utf-8')
                else:
                    return str(txt_data)
            return ""
        
        except Exception as e:
            print(f"Error parsing DNS: {e}")
            return ""
    
    def download_file(self):
        """Download using stop and wait"""
        chunk_index = 0
        chunks = []
        timeout = 0
        max_timeout = 3
        
        while timeout < max_timeout:
            try:
                # Create and request DNS query
                query = self.create_dns_query(chunk_index)
                
                self.socket.sendto(query, (self.dns_server_ip, self.dns_server_port))
                
                # Waiting for response
                response, _ = self.socket.recvfrom(4096)
                
                # Extracting data
                chunk_data = self.parse_dns_response(response)
                
                # If we get an empty chunk(end of the file)
                if not chunk_data:
                    print(f"Download done.")
                    break
                
                # Adding chunk to chunks list
                chunks.append(chunk_data)
                
                # Next chunk
                chunk_index += 1
                timeout = 0  # Timeout reset

                # Printing received chunk for debugging
                decoded_chunk = base64.b64decode(chunk_data)
                print(f"Received chunk {chunk_index}: {decoded_chunk[:25]}...")
                
            except socket.timeout:
                timeout += 1
                print(f"Timeout {timeout}")
            
            except Exception as e:
                print(f"Error: {e}")
                timeout += 1
                if timeout >= max_timeout:
                    break
        
        if chunks:
            # Decode and append data
            complete_data = ''.join(chunks)
            try:
                decoded_data = base64.b64decode(complete_data)
                
                # Saving the data
                output_file = f"received_files/{self.file_name}_received.txt"
                with open(output_file, 'wb') as f:
                    f.write(decoded_data)
                
                return True
            
            except Exception as e:
                print(f"Error: {e}")
                return False
        else:
            print("No data received.")
            return False

if __name__ == "__main__":
    # Get filename or use "example" as default
    file_name = sys.argv[1] if len(sys.argv) > 1 else "example"
    
    client = DNSTunnelingClient(file_name=file_name)
    client.download_file()