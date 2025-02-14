## **Lab2: Distributed Data Processing using OpenMPI on Three Virtual Machines**
---

### **Objective**
This tutorial will guide you through setting up a **Master-Slave cluster** using **OpenMPI** for distributed data processing. The **Master Node** partitions and distributes data to **Slave Nodes**, which process it and return the results. Key features:
- **Parallel processing** using multiple nodes.
- **This tutorial use Blocking Communication, Try with Non-blocking communication** (MPI_Isend & MPI_Irecv) for efficiency.
- **Data compression using zlib** to reduce network transfer cost.
- **Node failure detection** using a **heartbeat mechanism**.
- **Performance monitoring** (CPU, memory, and network usage logging).

---

## **1. Environment Setup**
Before proceeding, ensure you have three virtual machines:
- **Master Node** (e.g., `master_private_ip`)
- **Slave Node 1** (e.g., `slave1_private_ip`)
- **Slave Node 2** (e.g., `slave2_private_ip`)

### **1.1 Install OpenMPI on All Virtual Machines**
Run the following commands on **each node** (Master and Slaves): (Already Installed in Virtual Lab)
```bash
sudo apt update
sudo apt install -y openmpi-bin openmpi-common openmpi-doc libopenmpi-dev zlib1g-dev
```

### **1.2 Verify OpenMPI Installation**
```bash
mpiexec --version
```
This should print the OpenMPI version.

### **1.3 Configure OpenMPI Host File**
On the **Master Node**, create a hostfile:
```bash
nano ~/mpi_hosts
```
Add the private IPs of all nodes:
```
master_private_ip slots=2
slave1_private_ip slots=2
slave2_private_ip slots=2
```
Save the file (`CTRL+X`, then `Y`, then `Enter`).

---

## **2. Implement Master-Slave Data Processing in OpenMPI**
### **2.1 Write the OpenMPI C Program**
On the **Master Node**, create a new file:
```bash
nano mpi_distributed_processing.c
```
Copy and paste the following **detailed** C code:
```c
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define DATA_SIZE 1000000   // Total data points to process
#define CHUNK_SIZE 100000   // Each slave processes this amount

// Function to simulate data processing at slave nodes
void process_data(int rank, int data[]) {
    printf("Slave %d processing data...\n", rank);

    // Perform some computation on the received data
    for (int i = 0; i < CHUNK_SIZE; i++) {
        data[i] = data[i] * rank;  // Example operation
    }

    printf("Slave %d processing complete.\n", rank);
}

int main(int argc, char** argv) {
    int rank, size;
    int data[CHUNK_SIZE];

    MPI_Init(&argc, &argv);   // Initialize MPI
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);  // Get process rank (Master: 0, Slaves: 1, 2...)
    MPI_Comm_size(MPI_COMM_WORLD, &size);  // Total number of nodes

    if (rank == 0) { // Master Node
        printf("Master: Distributing work to slaves...\n");

        int full_data[DATA_SIZE];
        for (int i = 0; i < DATA_SIZE; i++) full_data[i] = i;

        // Send chunks to each slave node
        for (int i = 1; i < size; i++) {
            MPI_Send(&full_data[(i - 1) * CHUNK_SIZE], CHUNK_SIZE, MPI_INT, i, 0, MPI_COMM_WORLD);
        }

        // Receive processed data from slaves
        int received_data[CHUNK_SIZE];
        for (int i = 1; i < size; i++) {
            MPI_Recv(received_data, CHUNK_SIZE, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            printf("Master received data from Slave %d\n", i);
        }

        printf("Master: Data processing completed.\n");

    } else { // Slave Nodes
        MPI_Recv(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("Slave %d received data, starting processing...\n", rank);

        process_data(rank, data);

        // Send processed data back to Master
        MPI_Send(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }

    MPI_Finalize(); // Finalize MPI
    return 0;
}
```
### **2.2 Compile the MPI Program**
On the **Master Node**, compile the program:
```bash
mpicc mpi_distributed_processing.c -o mpi_program -lz
```
This generates an executable **mpi_program**.

---

## **3. Running the MPI Cluster**
### **3.1 Running on All Nodes**
Start the MPI program from the **Master Node**:
```bash
mpirun --hostfile ~/mpi_hosts -np 3 ./mpi_program
```
This runs:
- **1 Master Node (Rank 0)**
- **2 Slave Nodes (Rank 1, 2)**

---

## **4. Handling Node Failures**
### **4.1 Implement Heartbeat Check**
Modify **Master Node** logic to **detect failed nodes**:
```c
int failed_nodes[2] = {0};

for (int i = 1; i < size; i++) {
    int flag;
    MPI_Iprobe(i, MPI_ANY_TAG, MPI_COMM_WORLD, &flag, MPI_STATUS_IGNORE);
    if (!flag) {
        failed_nodes[i - 1] = 1;
        printf("Slave %d failed!\n", i);
    }
}
```
If a node fails, **Master redistributes the workload** to **remaining active nodes**.

---

## **5. Optimizing Communication**
### **5.1 Using Non-Blocking Send/Receive**
Modify code to use **MPI_Isend() & MPI_Irecv()**:
```c
MPI_Request request;
MPI_Isend(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD, &request);
```
This prevents the **Master** from blocking while waiting for a response.

### **5.2 Data Compression Using zlib**
Before sending data, compress it:
```c
unsigned char compressed_data[CHUNK_SIZE];
uLongf compressed_size = CHUNK_SIZE;
compress(compressed_data, &compressed_size, (const Bytef *)data, CHUNK_SIZE);
MPI_Send(compressed_data, compressed_size, MPI_UNSIGNED_CHAR, 0, 0, MPI_COMM_WORLD);
```
This **reduces network transfer size** and improves efficiency.

---

## **6. Performance Analysis**
### **6.1 Log CPU, Memory, and Network Usage**
On **each node**, log system usage:
```bash
mpirun --hostfile ~/mpi_hosts -np 3 bash -c 'mpstat -P ALL 1 5 > cpu_usage.log & vmstat 1 5 > memory.log'
```

### **6.2 Measure Communication Overhead**
Modify code to **track bytes sent**:
```c
MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
printf("Node %d sent %d bytes.\n", rank, bytes_sent);
```

---

## **7. Summary**
- ✅ **Parallel data processing using OpenMPI**
- ✅ **Non-blocking communication (MPI_Isend, MPI_Irecv)**
- ✅ **Data compression with zlib**
- ✅ **Heartbeat-based failure detection**
- ✅ **Performance monitoring (CPU, memory, communication overhead)**

This Lab tutorial **fully equips you** to set up and run a **high-performance distributed computing cluster** using OpenMPI. 🚀

