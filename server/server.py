import socket
import threading
from datetime import datetime
from collections import defaultdict

# Constants
BUFFER = 1024
PORT = 5000
HOST = '0.0.0.0'  # Instead of 'localhost'
MAX_CLIENTS = 3
CURRENT_CLIENT_NUMBER = 1

class Server:
    def __init__(self):
        # Server properties
        self.host = HOST
        self.port = PORT
        self.clients = {}  # track connected clients (stores data like => [socket]: client_name)
        self.client_connection_times = defaultdict(dict) # use default dict to get() an unset end_time without an error (stores data like => client_name: {start_time, end_time})
        self.current_client_number = CURRENT_CLIENT_NUMBER
        self.available_numbers = list(range(1, MAX_CLIENTS+1)) # where client numbers are assigned from
        self.lock = threading.Lock() # acquire lock to prevent race condition in accessing a shared socket resource
        
        # Server initialization
        # use ipv4 addresses (AF_INET) and a TCP connection (SOCK_STREAM) to establish a reliable and ordered connection
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # configure socket options to ensure addresses cannot be reused (option = 0 (false))
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        # reserve IP address and port (localhost:5000) for this server so that no other connections on my machine can use the same connection
        self.server_socket.bind((self.host, self.port))
        
        self.server_socket.listen(MAX_CLIENTS)
        
    def get_client_name(self):
        with self.lock: # use lock to prevent other threads accessing the current_client_number property at the same time
            if not self.available_numbers: return None
            number = min(self.available_numbers)
            self.available_numbers.remove(number) # remove number so as to indicate that a client with this number is connected
            return f"Client{number:02d}"

    def handle_client_request(self, client_socket, client_address):
        client_name = self.get_client_name()
        # convert client name into bytes to send it via tcp connection
        client_socket.send(client_name.encode())
        # track clients
        self.clients[client_socket] = client_name
        
        # end_time will default to "Active" if it is not set
        self.client_connection_times[client_name]['start_time'] = datetime.now()
        print(f"{client_name} connected from {client_address}")

        # Listen for incoming requests
        while True:
            try:
                message: str = client_socket.recv(BUFFER).decode() # bytes -> string
                # case #1: empty string
                if not message:
                    continue
                # case #2: exit
                if message.lower() == 'exit':
                    break
                # case #3: status
                elif message.lower() == 'status':
                    status = self.get_cache()
                    client_socket.send(status.encode())
                # case #4: valid message
                else:
                    response = f"{message} ACK"
                    client_socket.send(response.encode())

            except Exception as e:
                print(f"Error handling {client_name}: {e}")
                break

        # client sent "exit" perform disconnection
        self.disconnect_client(client_socket, client_name)

    def disconnect_client(self, client_socket, client_name):
        self.client_connection_times[client_name]['end_time'] = datetime.now() # update connection end time
        client_socket.close() # close socket
        del self.clients[client_socket] # delete client from clients object
        
        with self.lock:
            client_number = int(client_name.replace("Client", "")) # get client number itself (e.g. 1, 2, or 3)
            if client_number not in self.available_numbers: self.available_numbers.append(client_number)
            
        print(f"{client_name} disconnected")

    def get_cache(self):
        status = "\n=================================\nCurrent clients and their session information:\n=================================\n"
        
        for client, cached_time in self.client_connection_times.items():
            start_time = cached_time.get('start_time', 'N/A') # default to N/A
            end_time = cached_time.get('end_time', 'Active') # default to Active
            
            status += f"{client}: Start={start_time}, End={end_time}\n"
        return status


    def listen(self):
        print(f"Server started on {self.host}:{self.port}")
        print(f"Maximum clients allowed: {MAX_CLIENTS}")
        
        while True:
            try:
                # accept connections
                # client_socket is a socket object
                # client_address is the address (hostaddr, port) of the client
                client_socket, client_address = self.server_socket.accept()
                
                if len(self.clients) >= MAX_CLIENTS:
                    client_socket.send(f"The Server is currently at capacity with {MAX_CLIENTS} connections.\nPlease try again later.".encode())
                    client_socket.close()
                    continue
                
                # each client is handled inside a thread
                client_thread = threading.Thread(
                    target=self.handle_client_request,
                    args=(client_socket, client_address) # pass necessary arguments to the target
                )
                client_thread.start()
                
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break

        self.server_socket.close()

if __name__ == "__main__":
    server = Server()
    server.listen()