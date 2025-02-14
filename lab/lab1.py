import socket
import ssl
import threading
import psutil
import time

# Function to create an SSL context for secure communication
# - For the master node: Loads server certificate and key
# - For the slave node: Disables hostname verification for testing purposes
def create_ssl_context(server=True):
    if server:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    else:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False  # Disable hostname verification
        context.verify_mode = ssl.CERT_NONE  # Disable certificate verification (for testing)
    return context

# Master Node Class
class MasterNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.slaves = {}  # Dictionary to track connected slaves and last heartbeat time
        self.lock = threading.Lock()  # Mutex lock for thread safety

    def start(self):
        """Starts the master node, listens for incoming connections, and handles slaves."""
        context = create_ssl_context(server=True)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)  # Listen for up to 5 connections
            print(f"Master Node listening on {self.host}:{self.port}")

            with context.wrap_socket(server_socket, server_side=True) as secure_socket:
                while True:
                    client_socket, addr = secure_socket.accept()
                    print(f"Slave connected: {addr}")
                    threading.Thread(target=self.handle_slave, args=(client_socket, addr)).start()

    def handle_slave(self, client_socket, addr):
        """Handles communication with a connected slave node."""
        with client_socket:
            while True:
                try:
                    data = client_socket.recv(1024).decode()
                    if not data:
                        break

                    if data.startswith("HEARTBEAT"):
                        # Update last heartbeat time for the slave
                        with self.lock:
                            self.slaves[addr] = time.time()
                        print(f"Heartbeat received from {addr}")

                    elif data.startswith("RESOURCE"):
                        # Handle resource data received from the slave
                        resource_data = data.split(" ", 1)[1]
                        print(f"Resource data from {addr}: {resource_data}")
                except (ConnectionResetError, ssl.SSLError):
                    print(f"Connection lost with {addr}")
                    break

        # Remove the slave from the tracking list upon disconnection
        with self.lock:
            if addr in self.slaves:
                del self.slaves[addr]

    def monitor_slaves(self):
        """Monitors slaves to check for inactive or unresponsive nodes."""
        while True:
            with self.lock:
                now = time.time()
                for addr, last_heartbeat in list(self.slaves.items()):
                    if now - last_heartbeat > 10:  # If no heartbeat for 10 seconds, mark as unresponsive
                        print(f"Slave {addr} is unresponsive")
                        del self.slaves[addr]
            time.sleep(5)  # Check every 5 seconds

# Slave Node Class
class SlaveNode:
    def __init__(self, master_host, master_port):
        self.master_host = master_host
        self.master_port = master_port

    def start(self):
        """Connects to the master node and sends periodic heartbeats and resource status."""
        context = create_ssl_context(server=False)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as slave_socket:
            with context.wrap_socket(slave_socket, server_hostname=self.master_host) as secure_socket:
                secure_socket.connect((self.master_host, self.master_port))

                # Start separate threads for sending heartbeat and resource data
                threading.Thread(target=self.send_heartbeat, args=(secure_socket,), daemon=True).start()
                threading.Thread(target=self.send_resource_status, args=(secure_socket,), daemon=True).start()

                # Keep the connection alive
                while True:
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("Slave shutting down...")
                        break

    def send_heartbeat(self, secure_socket):
        """Sends a heartbeat message to the master node every 5 seconds."""
        while True:
            try:
                secure_socket.sendall(b"HEARTBEAT")
                time.sleep(5)
            except (ssl.SSLError, BrokenPipeError):
                print("Error sending heartbeat. Reconnecting...")
                break

    def send_resource_status(self, secure_socket):
        """Sends CPU and memory usage data to the master node every 10 seconds."""
        while True:
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                resource_data = f"CPU: {cpu}%, Memory: {memory}%"
                secure_socket.sendall(f"RESOURCE {resource_data}".encode())
                time.sleep(10)
            except (ssl.SSLError, BrokenPipeError):
                print("Error sending resource status. Reconnecting...")
                break

# Main Execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py [master|slave]")
        sys.exit(1)

    if sys.argv[1] == "master":
        master = MasterNode("127.0.0.1", 8000)  # Bind master node to all interfaces on port 8000
        threading.Thread(target=master.monitor_slaves, daemon=True).start()
        master.start()

    elif sys.argv[1] == "slave":
        slave = SlaveNode("127.0.0.1", 8000)  # Connect to master node on localhost
        slave.start()

    else:
        print("Invalid argument. Use 'master' or 'slave'.")
