import socket
import threading

# Constants (use the same connection-suite as the server)
HOST = 'server'  # If using docker-compose, use the service name
PORT = 5000

class Client:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        # setup ipv4 socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # will be assigned by the server
        self.client_name = None

    def receive_messages(self):
        while True:
            try:
                # open up socket to receive
                message = self.client_socket.recv(1024).decode()
                 # when server doesn't respond with a message 
                if not message:
                    print("Disconnected from server")
                    break
                # otherwise forward message to user
                print(f"\n{message}")
                # get instant output with flush to ensure that there is minimal delay between the client and the server
                print("Enter message (or 'exit' to quit): ", end='', flush=True)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
        self.client_socket.close()
    
    def relay_messages(self):
        # thread #1: to send messages to the server
        while True:
            message = input("Enter message (or 'exit' to quit): ")
            # case #1: exit
            if message.lower() == 'exit':
                self.client_socket.send(message.encode())
                break
            # case #2: regular message
            self.client_socket.send(message.encode())

    def connect(self):
        try:
            # setup a socket using "localhost:5000"
            self.client_socket.connect((self.host, self.port))
            
            # get the client name from the server
            self.client_name = self.client_socket.recv(1024).decode()
    
            # server relayed that the server is at capacity
            if self.client_name.startswith("Server is currently at capacity"):
                print(self.client_name) # forward the error message to the user
                self.client_socket.close()
                return
                
            # otherwise the server will send the name of the client
            print(f"Connected to server as {self.client_name}")
            
            # thread #2: daemon thread to run in the background continuously to pick up messages sent by server, but dies when the server terminates
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.relay_messages()
                
        except Exception as e:
            print(f"Error connecting to server: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    client = Client()
    client.connect()