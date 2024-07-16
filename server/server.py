import socket
import ssl
import argparse
import concurrent.futures
import traceback

class GenericServer:

    def __init__(self, server_addr='0.0.0.0', server_port=5555):
        self.server_port = server_port

        # Socket configuration
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((server_addr, server_port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(10)

        # SSL configuration
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(certfile='server_cert.pem', keyfile='server_key.pem')

        # Server variables
        self.active = True

    def run(self):
        """Main loop to accept and handle client connections."""
        try:
            while self.active:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Wrap socket with SSL
                    ssl_client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                    new_client = ClientHandler(ssl_client_socket, client_address)
                    new_client.handle_client()
                
                except socket.timeout:
                    # Continue to accept new connections after timeout
                    continue
                
                except ssl.SSLError as e:
                    print(f"SSL error: {e}")
                
                except Exception as e:
                    print(f"Server error: {e}")
                    print(traceback.format_exc())

        except Exception as e:
            print(f"Server error: {e}")
        
        finally:
            self.server_socket.close()
            print("Server shutdown.")

class ClientHandler:

    def __init__(self, conn, addr):
        self.client_addr, self.client_port = addr
        self.conn = conn

    def handle_client(self):
        """Handles the interaction with a connected client."""
        # Use a thread to handle client communication
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.run)

    def run(self):
        """Main logic for client communication."""
        with self.conn:
            print(f'Connection from {self.client_addr} port {self.client_port}')
            try:
                while True:
                    # Replace the following with application-specific logic
                    data = self.conn.recv(1024)
                    if not data:
                        break
                    # Echo received data (example)
                    self.conn.sendall(data)
            except Exception as e:
                print(f"Client handler error: {e}")
            finally:
                print(f"Connection closed from {self.client_addr} port {self.client_port}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--server-port", default=5555, type=int, help="Server port")
    args = parser.parse_args()

    server = GenericServer(server_port=args.server_port)

    # Use concurrent futures to run the server
    with concurrent.futures.ThreadPoolExecutor() as executor:
        try:
            executor.submit(server.run)
        except KeyboardInterrupt:
            server.active = False
            print("Server stopped")
