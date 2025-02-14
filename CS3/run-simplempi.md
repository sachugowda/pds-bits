To run a simple "Hello World" program using OpenMPI, follow these steps:

### **Step 1: Install OpenMPI**
If OpenMPI is not installed, install it using:
```bash
sudo apt update
sudo apt install openmpi-bin openmpi-common libopenmpi-dev
```

### **Step 2: Create a Simple "Hello World" MPI Program**
Create a file named `hello_mpi.c`:
```c
#include <mpi.h>  // Include the MPI library header, required for MPI functions
#include <stdio.h> // Include standard I/O library for printf

int main(int argc, char** argv) {
    // Initialize the MPI execution environment
    // This function sets up the MPI environment and must be called before any MPI functions
    MPI_Init(&argc, &argv);

    int world_size, world_rank; // Variables to store total number of processes and current process rank

    // Get the total number of processes in the communicator (MPI_COMM_WORLD)
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    // Get the rank (unique identifier) of the current process
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    // Print a message from each process
    // Each process will execute this independently, printing its rank and the total number of processes
    printf("Hello from process %d out of %d\n", world_rank, world_size);

    // Finalize the MPI environment
    // This function should be the last MPI call in a program
    // It cleans up MPI state and must be called before the program exits
    MPI_Finalize();

    return 0; // Exit the program successfully
}

```

### **Step 3: Compile the Program**
Use `mpicc` (MPI C compiler wrapper) to compile:
```bash
mpicc hello_mpi.c -o hello_mpi
```

### **Step 4: Run the Program**
Run it with multiple processes (e.g., 4 processes):
```bash
mpirun -np 4 ./hello_mpi
```

### **Expected Output**
Each process will print:
```
Hello from process 0 out of 4
Hello from process 1 out of 4
Hello from process 2 out of 4
Hello from process 3 out of 4
```
The order of messages may vary.
