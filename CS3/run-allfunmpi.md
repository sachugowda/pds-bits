Here’s a simple MPI program that demonstrates all the functions mentioned. This program can be executed in a single-node MPI setup (e.g., on WSL with OpenMPI installed).

### **MPI Program:**

```c
#include <mpi.h>  // Include MPI library
#include <stdio.h> // Standard I/O

int main(int argc, char** argv) {
    // 1. Initialize the MPI environment
    MPI_Init(&argc, &argv);
    // Now the program is running in a distributed manner

    // 2. Determine the number of processes (total processes in the communicator)
    int world_size;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    // 3. Determine the rank (ID) of the current process
    int world_rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    // 4. Example of point-to-point communication using MPI_Send and MPI_Recv
    if (world_rank == 0) {
        // Process 0 (sender)
        int data_to_send = 42;  // Example data to send
        MPI_Send(&data_to_send, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);  // Send data to process 1
        printf("Process %d sent data %d to process 1\n", world_rank, data_to_send);
    } else if (world_rank == 1) {
        // Process 1 (receiver)
        int received_data;  // Variable to store received data
        MPI_Recv(&received_data, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE); // Receive data from process 0
        printf("Process %d received data %d from process 0\n", world_rank, received_data);
    }

    // 5. Finalize the MPI environment
    MPI_Finalize();
    // The program terminates gracefully, and all resources are freed
    return 0;
}
```

---

### **Explanation in Comments:**
1. **`MPI_Init(&argc, &argv);`**
   - Initializes the MPI environment. It must be called before using any other MPI functions.
2. **`MPI_Comm_size(MPI_COMM_WORLD, &world_size);`**
   - Determines the total number of processes participating in the communicator.
3. **`MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);`**
   - Retrieves the rank (ID) of the current process. Each process gets a unique rank starting from 0.
4. **`MPI_Send()` and `MPI_Recv()`**
   - Process 0 sends data (`MPI_Send`), and Process 1 receives it (`MPI_Recv`).
   - These are used for point-to-point communication.
5. **`MPI_Finalize();`**
   - Cleans up the MPI environment and ensures all processes terminate gracefully.

---

### **Compiling and Running the Program in WSL**

#### **1. Install OpenMPI (if not already installed):**
```bash
sudo apt update
sudo apt install openmpi-bin openmpi-common libopenmpi-dev -y
```

#### **2. Save the Program**
Save the program as `mpi_example.c`:
```bash
nano mpi_example.c
```
Paste the code and save (`Ctrl+X`, `Y`, `Enter`).

#### **3. Compile the Program**
Use `mpicc` to compile the program:
```bash
mpicc mpi_example.c -o mpi_example
```

#### **4. Run the Program with Multiple Processes**
Use `mpirun` to execute the program:
```bash
mpirun -np 2 ./mpi_example
```
- `-np 2`: Runs the program with 2 processes.

---

### **Expected Output**
When executed with 2 processes, you should see:
```
Process 0 sent data 42 to process 1
Process 1 received data 42 from process 0
```

This output demonstrates:
1. Process 0 sending data to Process 1 using `MPI_Send`.
2. Process 1 receiving the data using `MPI_Recv`.

---
