### **Running OpenMPI Program on 3 Different Virtual Machines**



---

### **Step 1: Configure the Hostfile**
The hostfile lists all nodes (master and workers) participating in the MPI program.

#### **Steps (Run on Server 1 only):**
1. Create a hostfile:
   ```bash
   nano ~/mpi_hosts
   ```
2. Add the following lines (use private IPs for communication):
   ```
   172.31.14.206 slots=2  # Server 1 (Master)
   172.31.15.127 slots=2  # Server 2 (Worker)
   172.31.4.202  slots=2  # Server 3 (Worker)
   ```
   Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

---

### **Step 2: Write and Compile the MPI Program**
Write a simple MPI "Hello World" program.

#### **Steps (Run on Server 1 only):**
1. Create a new file:
   ```bash
   nano hello_mpi.c
   ```
2. Add the following code:
   ```c
   #include <mpi.h>
   #include <stdio.h>

   int main(int argc, char** argv) {
       MPI_Init(&argc, &argv);

       int world_size, world_rank;
       MPI_Comm_size(MPI_COMM_WORLD, &world_size);
       MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

       printf("Hello from process %d out of %d\n", world_rank, world_size);

       MPI_Finalize();
       return 0;
   }
   ```
3. Save and exit.

---

### **Step 3: Compile the MPI Program**
Compile the program using `mpicc`.

#### **Steps (Run on Server 1 only):**
1. Compile the code:
   ```bash
   mpicc hello_mpi.c -o hello_mpi
   ```
2. Copy the compiled file to worker nodes:
   ```bash
   scp hello_mpi labuser@172.31.15.127:~/  # Copy to Server 2
   scp hello_mpi labuser@172.31.4.202:~/   # Copy to Server 3
   ```

---

### **Step 4: Run the MPI Program**
Run the MPI program across all three servers.

#### **Steps (Run on Server 1 only):**
1. Execute the program using `mpirun`:
   ```bash
   mpirun --hostfile ~/mpi_hosts -np 6 ./hello_mpi
   ```
   - `--hostfile ~/mpi_hosts`: Specifies the list of nodes (master and workers).
   - `-np 6`: Runs 6 processes (2 per node).
   - `./hello_mpi`: Executes the compiled MPI program.

---

### **Expected Output**
If everything is set up correctly, you will see output similar to:
```
Hello from process 0 out of 6
Hello from process 1 out of 6
Hello from process 2 out of 6
Hello from process 3 out of 6
Hello from process 4 out of 6
Hello from process 5 out of 6
```

Each line corresponds to one process running on a specific node.

---
