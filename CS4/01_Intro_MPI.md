# **Module 2: Distributed Memory Programming with MPI**
---
## **1. Introduction to Distributed Memory Programming**
### **1.1 Parallel Computing Architectures**
Parallel computing architectures are classified into **Shared-Memory Systems** and **Distributed-Memory Systems**:
- **Shared-Memory System:** All processors (cores) share a **single global memory** and can directly access it. Communication is done using shared variables (Figure 3.2 in Text Book 1).
- **Distributed-Memory System:** Each processor (core) has **its own local memory**. Communication between processors occurs via **message-passing** over a network (Figure 3.1 in Text Book 1).

### **1.2 Understanding Distributed Memory Systems**
In a **distributed-memory system**, memory associated with a processor is **only accessible by that processor**. Communication between processors requires **explicit message-passing**, making it different from shared-memory programming, where memory is globally accessible.

---
## **2. Message Passing with MPI**
### **2.1 What is MPI?**
**MPI (Message-Passing Interface)** is a **standardized library** for message-passing in distributed-memory systems. It is not a new programming language but a collection of functions that can be used in **C and Fortran**.

### **2.2 Key Features of MPI**
- **Allows inter-process communication** in distributed-memory systems.
- **Scalable** for running on hundreds or thousands of processes.
- **Portable** and works across different HPC (High-Performance Computing) clusters.
- **Supports synchronous (blocking) and asynchronous (non-blocking) communication.**

---
## **3. Basics of MPI Programming**
### **3.1 Understanding MPI Processes**
- An **MPI process** is a program instance running on a core-memory pair.
- Each process has a unique **rank (ID)** within an MPI **communicator**.
- Multiple processes are executed in **parallel** with explicit communication.

### **3.2 Writing an MPI Program**
MPI programs follow a **Single Program, Multiple Data (SPMD)** model, meaning:
- The same program is executed by **all processes**.
- Each process performs different tasks based on **its rank**.

### **3.3 Example: MPI "Hello World"**
The following **MPI program** initializes MPI, assigns ranks to processes, and prints a message from each process.

#### **C Code for Basic MPI Communication**
```c
#include <stdio.h>
#include <string.h>  // For strlen
#include <mpi.h>     // For MPI functions

const int MAX_STRING = 100;

int main(void) {
    char greeting[MAX_STRING];
    int comm_sz;   // Number of processes
    int my_rank;   // Process rank

    MPI_Init(NULL, NULL);  // Initialize MPI
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);  // Get total number of processes
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);  // Get rank of this process

    if (my_rank != 0) { // Non-Master processes
        sprintf(greeting, "Greetings from process %d of %d!", my_rank, comm_sz);
        MPI_Send(greeting, strlen(greeting) + 1, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
    } else { // Master process (Rank 0)
        printf("Greetings from process %d of %d!\n", my_rank, comm_sz);
        for (int q = 1; q < comm_sz; q++) {
            MPI_Recv(greeting, MAX_STRING, MPI_CHAR, q, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            printf("%s\n", greeting);
        }
    }

    MPI_Finalize();  // Finalize MPI
    return 0;
}
```

### **3.4 Explanation of the Code**
- **Line 3-4:** Includes standard C and MPI headers.
- **Line 9-10:** Defines variables for process rank and total process count.
- **Line 12:** Initializes MPI (`MPI_Init`).
- **Line 13-14:** Retrieves the number of processes (`MPI_Comm_size`) and assigns ranks (`MPI_Comm_rank`).
- **Line 16-21:** Processes with rank **not 0** send messages to process 0 using `MPI_Send`.
- **Line 22-29:** **Master process (Rank 0)** receives messages from other processes (`MPI_Recv`) and prints them.
- **Line 31:** Finalizes MPI (`MPI_Finalize`).

---
## **4. Compilation and Execution of MPI Programs**
### **4.1 Compilation**
To compile an MPI program, use the **mpicc** compiler:
```bash
mpicc -g -Wall -o mpi_hello mpi_hello.c
```
- `-g` → Enables debugging.
- `-Wall` → Shows all warnings.
- `-o mpi_hello` → Generates an executable named `mpi_hello`.

### **4.2 Execution**
To run the MPI program using **mpiexec**:
```bash
mpiexec -n <number_of_processes> ./mpi_hello
```
#### **Example Runs**
```bash
mpiexec -n 1 ./mpi_hello
```
**Output (1 process):**
```
Greetings from process 0 of 1!
```
```bash
mpiexec -n 4 ./mpi_hello
```
**Output (4 processes):**
```
Greetings from process 0 of 4!
Greetings from process 1 of 4!
Greetings from process 2 of 4!
Greetings from process 3 of 4!
```
---
## **5. MPI Communication and Performance Considerations**
### **5.1 Message-Passing in MPI**
MPI supports **two** types of communication:
1. **Point-to-Point Communication**: Between two processes.
   - **Blocking**: `MPI_Send`, `MPI_Recv` (Waits for completion).
   - **Non-blocking**: `MPI_Isend`, `MPI_Irecv` (Allows overlapping computation and communication).
2. **Collective Communication**: Among multiple processes.
   - **Broadcast (`MPI_Bcast`)**: One process sends data to all.
   - **Scatter (`MPI_Scatter`)**: Master distributes different parts of data.
   - **Gather (`MPI_Gather`)**: All processes send data to Master.

---
## **6. Communication Cost Analysis**
MPI communication introduces **costs** due to **latency, bandwidth, and payload size**:
1. **Latency**: Time taken for the message to start reaching its destination.
2. **Bandwidth**: Rate at which data is transferred (MB/s).
3. **Payload Size**: Amount of data transferred in each message.

### **Measuring Communication Cost in MPI**
To measure **transfer time**, modify the program:
```c
double start_time, end_time;
start_time = MPI_Wtime();  // Start time
MPI_Send(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD);
end_time = MPI_Wtime();  // End time
printf("Process %d: Transfer time = %f seconds\n", rank, end_time - start_time);
```
Formula for **Bandwidth Calculation**:
Bandwidth = Payload Size / Transfer Time

---
## **7. Flow Control & Throttling in MPI**
### **7.1 What is Throttling?**
Throttling is the process of **limiting the data transfer rate** to prevent **network congestion**.

### **7.2 Why is Throttling Important?**
- Prevents network overload.
- Reduces **packet loss** and retransmissions.
- Ensures fair bandwidth allocation across processes.

### **7.3 Implementing Flow Control in MPI**
To **avoid sending too much data at once**, the **Master Node** can send data only when **Slaves acknowledge receipt**:
```c
int ack = 1;
MPI_Send(data, CHUNK_SIZE, MPI_INT, slave, 0, MPI_COMM_WORLD);
MPI_Recv(&ack, 1, MPI_INT, slave, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
```
---
## **8. Summary**
- **Distributed-memory systems** require explicit **message-passing** for inter-process communication.
- **MPI provides a scalable solution** for distributed computing.
- **Blocking (`MPI_Send`) vs. Non-Blocking (`MPI_Isend`) Communication.**
- **Performance metrics**: Latency, Bandwidth, and Payload Size.
- **Flow Control (Throttling)** prevents network congestion.

