# TCP client
import socket
import logging
import time
import sys
import random
import string
import threading

# configure logging to show only INFO level and above for cleaner output
logging.basicConfig(format = u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO)

# generating random messages
def generate_message():
    # mixed messages (letters + digits)
    chars = string.ascii_letters + string.digits
    # random length
    length = random.randint(10,20)
    # creating the message
    return ''.join(random.choices(chars, k=length))

def client_listener():
    """Function that listens for messages from server"""
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # bind to all interfaces to receive messages
        listen_sock.bind(('0.0.0.0', 10001))
        listen_sock.listen(5)
        
        while True:
            try:
                # accept connection from server
                conexiune, address = listen_sock.accept()
                
                # receive data from server
                data = conexiune.recv(1024)
                
                # ONLY show messages received from server
                print(f"SERVER MESSAGE: {data.decode('utf-8')}")
                
                # send confirmation back to server (silent)
                raspuns = f"Client confirms: {data.decode('utf-8')}"
                conexiune.send(raspuns.encode('utf-8'))
                conexiune.close()
                
            except Exception as e:
                pass  # Silent error handling
                
    except Exception as e:
        pass  # Silent error handling
    finally:
        listen_sock.close()

# start thread for listening to messages from server
thread_listen = threading.Thread(target=client_listener, daemon=True)
thread_listen.start()

# main client that sends messages to server
port = 10000
adresa = '198.7.0.2'  # server address
server_address = (adresa, port)

try:
    while True:
        # create a new socket for each connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        
        try:
            message = generate_message()
            sock.connect(server_address)
            time.sleep(3)
            sock.send(message.encode('utf-8'))
            data = sock.recv(1024)
            
        except Exception as e:
            pass  # silent error handling
        finally:
            sock.close()
            
        time.sleep(2)  # 5 seconds between messages
        
except KeyboardInterrupt:
    print("\nClient stopped by user")
except Exception as e:
    pass  # silent error handling
finally:
    print("Client closed")