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
## **3. Communicators and SPMD in MPI**
### **3.1 MPI Communicators**
A **communicator** in MPI is a collection of processes that can communicate with each other. MPI provides a default communicator called **MPI_COMM_WORLD**, which includes all processes started by the user.

Key MPI functions related to communicators:
```c
int MPI_Comm_size(MPI_Comm comm, int *comm_sz_p);  // Gets number of processes in a communicator
int MPI_Comm_rank(MPI_Comm comm, int *my_rank_p);  // Gets rank of calling process
```
- `MPI_Comm_size` returns the total number of processes in the communicator.
- `MPI_Comm_rank` returns the unique rank (ID) of the calling process.

### **3.2 SPMD (Single Program, Multiple Data) Model**
MPI programs follow the **Single Program, Multiple Data (SPMD)** paradigm, where:
- A single program is written and executed by all processes.
- Each process operates on its **own portion of data**.
- Process behavior is differentiated using **MPI rank**.

### **3.3 Example: MPI "Hello World" with Communicators and SPMD**
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

