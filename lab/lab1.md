# Tutorial: Implementing a Secure Master-Slave Cluster Management Protocol

This tutorial walks through the implementation of a secure master-slave cluster management system using Python. We will explain the code structure, the role of each component, and how to set it up and execute on your system.

## Objective
To build a system where a master node manages multiple slave nodes. The system includes:
- Secure communication between nodes using SSL/TLS.
- Periodic health monitoring (heartbeats).
- Resource usage reporting from slaves to the master.
- Fault tolerance with automatic reconnections.

---

## Code Breakdown

### 1. Setting Up SSL for Secure Communication
To ensure that the communication between nodes is encrypted and secure, we use SSL/TLS. The `create_ssl_context` function sets up different configurations for the master (server) and slave (client) nodes.

```python
# Secure SSL context setup
def create_ssl_context(server=True):
    if server:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    else:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False  # Disable hostname checking for client
        context.verify_mode = ssl.CERT_NONE  # Disable certificate verification for testing purposes
    return context
```

- **Server SSL Context:** Loads a certificate and private key for authentication.
- **Client SSL Context:** Disables hostname checking and certificate verification for simplicity (can be made stricter in production).

### 2. Master Node
The master node manages the cluster, keeps track of connected slaves, and monitors their health and resource usage.

#### Initialization
```python
class MasterNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.slaves = {}  # {address: last_heartbeat_time}
        self.lock = threading.Lock()
```
- **Attributes:**
  - `host` and `port`: Network configuration.
  - `slaves`: Dictionary to store the last heartbeat time from each slave.
  - `lock`: Ensures thread-safe access to the `slaves` dictionary.

#### Main Functions

1. **Start the Master:**
   Listens for incoming connections and starts a thread to handle each slave.

   ```python
   def start(self):
       context = create_ssl_context(server=True)
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
           server_socket.bind((self.host, self.port))
           server_socket.listen(5)
           print(f"Master Node listening on {self.host}:{self.port}")

           with context.wrap_socket(server_socket, server_side=True) as secure_socket:
               while True:
                   client_socket, addr = secure_socket.accept()
                   print(f"Slave connected: {addr}")
                   threading.Thread(target=self.handle_slave, args=(client_socket, addr)).start()
   ```

2. **Handle Slave Connections:**
   Processes heartbeats and resource updates from slaves.

   ```python
   def handle_slave(self, client_socket, addr):
       with client_socket:
           while True:
               try:
                   data = client_socket.recv(1024).decode()
                   if not data:
                       break

                   if data.startswith("HEARTBEAT"):
                       with self.lock:
                           self.slaves[addr] = time.time()
                       print(f"Heartbeat received from {addr}")

                   elif data.startswith("RESOURCE"):
                       resource_data = data.split(" ", 1)[1]
                       print(f"Resource data from {addr}: {resource_data}")

               except (ConnectionResetError, ssl.SSLError):
                   print(f"Connection lost with {addr}")
                   break
   ```

3. **Monitor Slaves:**
   Periodically checks for unresponsive slaves based on heartbeat timestamps.

   ```python
   def monitor_slaves(self):
       while True:
           with self.lock:
               now = time.time()
               for addr, last_heartbeat in list(self.slaves.items()):
                   if now - last_heartbeat > 10:  # 10-second timeout
                       print(f"Slave {addr} is unresponsive")
                       del self.slaves[addr]

           time.sleep(5)
   ```

### 3. Slave Node
The slave node sends periodic heartbeats and resource usage data to the master.

#### Initialization
```python
class SlaveNode:
    def __init__(self, master_host, master_port):
        self.master_host = master_host
        self.master_port = master_port
```

#### Main Functions

1. **Start the Slave:**
   Establishes a secure connection to the master and starts threads for sending heartbeats and resource data.

   ```python
   def start(self):
       context = create_ssl_context(server=False)
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as slave_socket:
           with context.wrap_socket(slave_socket, server_hostname=self.master_host) as secure_socket:
               secure_socket.connect((self.master_host, self.master_port))

               def send_heartbeat():
                   while True:
                       try:
                           secure_socket.sendall(b"HEARTBEAT")
                           time.sleep(5)
                       except (ssl.SSLError, BrokenPipeError):
                           print("Error sending heartbeat. Reconnecting...")
                           break

               def send_resource_status():
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

               threading.Thread(target=send_heartbeat, daemon=True).start()
               threading.Thread(target=send_resource_status, daemon=True).start()

               while True:
                   try:
                       time.sleep(1)  # Keep the connection alive
                   except KeyboardInterrupt:
                       print("Slave shutting down...")
                       break
   ```

---

## Execution Instructions

### 1. Generate SSL Certificates
Run the following command to generate `server.crt` and `server.key`:
```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
```

### 2. Install Dependencies
Install Python and the required libraries:
```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install psutil
```

### 3. Run the Master Node
Start the master node:
```bash
python3 cluster_management.py master
```

### 4. Run the Slave Nodes
Start one or more slave nodes:
```bash
python3 cluster_management.py slave
```

---

## Observing the Behavior
- The master node logs connections, heartbeats, and resource usage updates.
- If a slave node disconnects or fails to send heartbeats, the master logs it as unresponsive.

This completes the implementation and execution of the cluster management protocol. Let me know if you have any questions or issues!

