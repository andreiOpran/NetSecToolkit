# TCP Server
import socket
import logging
import time
import threading
import random
import string

# configure logging to show only INFO level and above for cleaner output
logging.basicConfig(format = u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO)

# generating random messages
def generate_message():
    # mixt messages
    chars = string.ascii_letters + string.digits
    # random length
    length = random.randint(10,20)
    # creating the message
    return ''.join(random.choices(chars, k=length))

def send_messages():
    """Sending messages to client"""
    while True:
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_address = ('172.7.0.2', 10001)  # client's listening port

            # trying to connect to clients address
            client_sock.connect(client_address)

            # generating a message
            message = generate_message()
            # sending the message
            client_sock.send(message.encode('utf-8'))

            # receiving messages (silent)
            response = client_sock.recv(1024)
            # Remove this logging to keep output clean
            # logging.info('Reply from client: "%s"', response.decode('utf-8'))

            client_sock.close()
            time.sleep(2)  # sending each 5 seconds

        except Exception as e:
            pass  # Silent error handling

# creating a thread to start the communication
sending_thread = threading.Thread(target=send_messages, daemon=True)
sending_thread.start()

# server config
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
# add SO_REUSEADDR to avoid "Address already in use" error
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 10000
adresa = '0.0.0.0'  # listening to every interface
server_address = (adresa, port)
sock.bind(server_address)
sock.listen(5)

while True:
    conexiune, address = sock.accept()
    time.sleep(2)
    data = conexiune.recv(1024)
    
    print(f"CLIENT MESSAGE: {data.decode('utf-8')}")
    
    conexiune.send(b"Server received the message: " + data)
    conexiune.close()

sock.close()