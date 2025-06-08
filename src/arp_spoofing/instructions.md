# ARP Spoofing instructions

## Terminal 1:

### docker-compose exec middle bash
### cd elocal/retele-broski-corporation/src/arp_spoofing
### source venv/bin/activate
### python3 arp_spoofing.py


## Terminal 2:

### docker-compose exec middle bash
### tcpdump -SntvXX -i any


## Terminal 3:

### docker-compose exec server bash
### wget http://old.fmi.unibuc.ro


### You can see the HTML content on Terminal 1, also in sniffed_packets/captured_packets.txt