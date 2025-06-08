# ARP Spoofing instructions

## Terminal 1:
docker-compose exec middle bash <br>
cd elocal/retele-broski-corporation/src/arp_spoofing<br>
source venv/bin/activate<br>
python3 arp_spoofing.py<br>

## Terminal 2:
docker-compose exec middle bash<br>
tcpdump -SntvXX -i any

## Terminal 3:
docker-compose exec server bash<br>
wget http://old.fmi.unibuc.ro

#### You can see the HTML content on Terminal 1, also in sniffed_packets/captured_packets.txt.