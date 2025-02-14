# Distributed Systems Tutorial: Nodes, Processes, and Communication

This tutorial provides a step-by-step guide to understanding and implementing key concepts in distributed systems. By the end of this tutorial, you will have hands-on experience with:

- Processes running on different machines.
- Secure communication using SSL.
- Master-slave architecture.
- Client-server communication using RPC.
- Node discovery and membership.
- Fault tolerance.

Each section includes code examples, exercises, and explanations to help you build and run distributed systems applications.

## 1. Processes Running on Different Machines
### Objective
Understand how processes run on different machines and communicate over a network.

### Example
- Machine A: Generates data (e.g., a random number).
- Machine B: Processes the data (e.g., receives the number).

### Exercise
- Set up two machines (or use two terminals on the same machine).
- Run a Python script on Machine A to generate a random number.
- Send the number to Machine B using a socket connection.

### Code Example
```python
# Machine A: Sender
import socket
import random

s = socket.socket()
s.bind(('0.0.0.0', 12345))  # Bind to port 12345
s.listen(1)
print("Machine A waiting for connection...")
conn, addr = s.accept()
print(f"Connected to {addr}")

data = str(random.randint(1, 100))
conn.send(data.encode())
print(f"Sent data: {data}")
conn.close()
```

```python
# Machine B: Receiver
import socket

s = socket.socket()
s.connect(('127.0.0.1', 12345))  # Replace with Machine A's IP
data = s.recv(1024).decode()
print(f"Received data: {data}")
s.close()
```

### Steps to Run
1. Run the Sender code on Machine A.
2. Run the Receiver code on Machine B.
3. Observe the data being sent and received.

## 2. Communication Using Sockets and SSL
### Objective
Learn how to secure communication using SSL.

### Exercise
1. Generate SSL certificates for Machine A and Machine B.
2. Use the `ssl` library to wrap the socket connection.

### Generate SSL Certificates
Run the following command to generate a self-signed certificate and key:
```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost" -nodes
```

### Code Example
```python
# Machine A: SSL Sender
import socket, ssl
import random

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

s = socket.socket()
s.bind(('localhost', 12345))
s.listen(1)
print("Machine A waiting for connection...")
conn, addr = s.accept()
secure_conn = context.wrap_socket(conn, server_side=True)

data = str(random.randint(1, 100))
secure_conn.send(data.encode())
print(f"Sent data: {data}")
secure_conn.close()
```

```python
# Machine B: SSL Receiver
import socket, ssl

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_verify_locations("server.crt")

s = socket.socket()
secure_conn = context.wrap_socket(s, server_hostname='localhost')
secure_conn.connect(('localhost', 12345))

data = secure_conn.recv(1024).decode()
print(f"Received data: {data}")
secure_conn.close()
```

### Steps to Run
1. Generate `server.crt` and `server.key` using OpenSSL.
2. Run the SSL Sender code on Machine A.
3. Run the SSL Receiver code on Machine B.
4. Observe the encrypted communication.

## 3. Master-Slave Architecture
### Objective
Implement a simple master-slave system.

### Example
- **Master Node**: Assigns tasks to slave nodes.
- **Slave Node**: Executes tasks and reports back.

### Code Example
```python
# Master Node
import socket

def assign_task(slave_ip, task):
    s = socket.socket()
    s.connect((slave_ip, 12345))
    s.send(str(task).encode())
    result = s.recv(1024).decode()
    print(f"Result from {slave_ip}: {result}")
    s.close()

assign_task('127.0.0.1', 5)  # Replace with actual IP
```

```python
# Slave Node
import socket

def compute_square(number):
    return number ** 2

s = socket.socket()
s.bind(('0.0.0.0', 12345))
s.listen(1)
print("Slave waiting for connection...")
conn, addr = s.accept()

task = int(conn.recv(1024).decode())
result = compute_square(task)
conn.send(str(result).encode())
conn.close()
```

### Steps to Run
1. Run the Slave Node code on one machine.
2. Run the Master Node code on another machine.
3. Observe the task assignment and result.

## 6. Fault Tolerance
### Objective
Implement basic fault tolerance by detecting node crashes and switching to a backup node.

### Updated Node Code
```python
# Node: Sends Heartbeats to Registry Server
import socket
import time

def send_heartbeat():
    while True:
        try:
            s = socket.socket()
            s.connect(('127.0.0.1', 12345))  # Connect to the registry server
            s.send(b"Heartbeat")  # Send a heartbeat message
            s.close()
            print("Heartbeat sent")
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
        time.sleep(3)  # Send a heartbeat every 3 seconds

send_heartbeat()
```

### Updated Registry Server Code
```python
# Registry Server with Fault Detection
import socket
import threading
import time

nodes = {}

def handle_client(conn, addr):
    nodes[addr] = time.time()
    print(f"Active nodes: {list(nodes.keys())}")
    conn.close()

def detect_failures():
    while True:
        for addr, last_seen in list(nodes.items()):
            if time.time() - last_seen > 10:
                print(f"Node {addr} failed")
                del nodes[addr]
        time.sleep(5)

s = socket.socket()
s.bind(('0.0.0.0', 12345))
s.listen(5)
print("Registry server started. Waiting for nodes...")

threading.Thread(target=detect_failures, daemon=True).start()
while True:
    conn, addr = s.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()
```

### Summary
- The Node program sends periodic heartbeat messages.
- The Registry Server tracks active nodes and detects failures.
- A failover mechanism can notify a backup node when the primary node fails.

This tutorial provides a strong foundation in distributed systems concepts.
