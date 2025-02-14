### **Block, Cyclic, and Block-Cyclic Partitioning: Explanation and Examples**

Below is a detailed explanation of **Block Partitioning**, **Cyclic Partitioning**, and **Block-Cyclic Partitioning**, combined with **simple array addition examples** implemented using MPI.

---

### **1. Block Partitioning**

#### **Explanation:**
In block partitioning, the data is divided into **consecutive chunks**, and each chunk is assigned to a process. Each process works on a **contiguous block** of data, which makes this method ideal for problems where processes need to work on large, sequential data.

#### **Example:**
- **Input Array**: [1, 2, 3, 4, 5, 6, 7, 8]
- **Number of Processes (P)**: 4
- **Block Size**: \( \text{N/P} = 8/4 = 2 \)

**Data Distribution**:
- Process 0: [1, 2]
- Process 1: [3, 4]
- Process 2: [5, 6]
- Process 3: [7, 8]

**Visualization**:
```
Input Array: [1, 2, 3, 4, 5, 6, 7, 8]
Process 0 -> [1, 2]
Process 1 -> [3, 4]
Process 2 -> [5, 6]
Process 3 -> [7, 8]
```

#### **Code:**
```c
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    int rank, size, N = 8;
    int A[N], B[N], C[N];  // Arrays for addition
    int local_A[2], local_B[2], local_C[2];  // Local arrays for each process

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        // Initialize arrays A and B on the root process
        for (int i = 0; i < N; i++) {
            A[i] = i + 1;       // A = [1, 2, 3, 4, 5, 6, 7, 8]
            B[i] = (N - i);     // B = [8, 7, 6, 5, 4, 3, 2, 1]
        }
    }

    // Scatter chunks of A and B to all processes
    MPI_Scatter(A, 2, MPI_INT, local_A, 2, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Scatter(B, 2, MPI_INT, local_B, 2, MPI_INT, 0, MPI_COMM_WORLD);

    // Perform addition on the local chunks
    for (int i = 0; i < 2; i++) {
        local_C[i] = local_A[i] + local_B[i];
    }

    // Gather results back to the root process
    MPI_Gather(local_C, 2, MPI_INT, C, 2, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        // Print the resultant array
        printf("Resultant Array (Block Partitioning): ");
        for (int i = 0; i < N; i++) printf("%d ", C[i]);  // Output: [9, 9, 9, 9, 9, 9, 9, 9]
        printf("\n");
    }

    MPI_Finalize();
    return 0;
}
```

---

### **2. Cyclic Partitioning**

#### **Explanation:**
In cyclic partitioning, the data elements are distributed in a **round-robin fashion** across processes. Each process gets **non-contiguous elements** that are evenly distributed, ensuring balanced workloads.

#### **Example:**
- **Input Array**: [1, 2, 3, 4, 5, 6, 7, 8]
- **Number of Processes (P)**: 4

**Data Distribution**:
- Process 0: [1, 5]
- Process 1: [2, 6]
- Process 2: [3, 7]
- Process 3: [4, 8]

**Visualization**:
```
Input Array: [1, 2, 3, 4, 5, 6, 7, 8]
Process 0 -> [1, 5]
Process 1 -> [2, 6]
Process 2 -> [3, 7]
Process 3 -> [4, 8]
```

#### **Code:**
```c
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    int rank, size, N = 8;
    int A[N], B[N], C[N];  // Arrays for addition
    int local_A[2], local_B[2], local_C[2];  // Local arrays for each process

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        // Initialize arrays A and B on the root process
        for (int i = 0; i < N; i++) {
            A[i] = i + 1;       // A = [1, 2, 3, 4, 5, 6, 7, 8]
            B[i] = (N - i);     // B = [8, 7, 6, 5, 4, 3, 2, 1]
        }
    }

    // Distribute elements cyclically
    for (int i = rank, index = 0; i < N; i += size, index++) {
        local_A[index] = A[i];
        local_B[index] = B[i];
    }

    // Perform addition on local elements
    for (int i = 0; i < 2; i++) {
        local_C[i] = local_A[i] + local_B[i];
    }

    // Gather results back to all processes
    MPI_Allgather(local_C, 2, MPI_INT, C, 2, MPI_INT, MPI_COMM_WORLD);

    if (rank == 0) {
        // Print the resultant array
        printf("Resultant Array (Cyclic Partitioning): ");
        for (int i = 0; i < N; i++) printf("%d ", C[i]);  // Output: [9, 9, 9, 9, 9, 9, 9, 9]
        printf("\n");
    }

    MPI_Finalize();
    return 0;
}
```

---

### **3. Block-Cyclic Partitioning**

#### **Explanation:**
In block-cyclic partitioning, the data is divided into **blocks of size `block_size`**, and these blocks are distributed cyclically among processes. It combines the **locality** of block partitioning with the **load balancing** of cyclic partitioning.

#### **Example:**
- **Input Array**: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
- **Number of Processes (P)**: 3
- **Block Size**: 2

**Data Distribution**:
- Process 0: [1, 2, 7, 8]
- Process 1: [3, 4, 9, 10]
- Process 2: [5, 6, 11, 12]

**Visualization**:
```
Input Array: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
Process 0 -> [1, 2, 7, 8]
Process 1 -> [3, 4, 9, 10]
Process 2 -> [5, 6, 11, 12]
```

#### **Code:**
```c
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
    int rank, size, N = 12, block_size = 2;
    int A[N], B[N], C[N];  // Arrays for addition
    int local_A[4], local_B[4], local_C[4];  // Local arrays for each process

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        // Initialize arrays A and B on the root process
        for (int i = 0; i < N; i++) {
            A[i] = i + 1;       // A = [1, 2, ..., 12]
            B[i] = (N - i);     // B = [12, 11, ..., 1]
        }
    }

    // Block-cyclic distribution
    int blocks_per_process = (N + block_size * size - 1) / (block_size * size);
    int total_elements = blocks_per_process * block_size;

    for (int b = 0; b < blocks_per_process; b++) {
        for (int i = 0; i < block_size; i++) {
            int global_index = (b * size + rank) * block_size + i;
            if (global_index < N) {
                local_A[b * block_size + i] = A[global_index];
                local_B[b * block_size + i] = B[global_index];
            }
        }
    }

    // Perform addition on local elements
    for (int i = 0; i < total_elements; i++) {
        local_C[i] = local_A[i] + local_B[i];
    }

    // Gather results back to the root process
    MPI_Gatherv(local_C, total_elements, MPI_INT, C, NULL, NULL, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        // Print the resultant array
        printf("Resultant Array (Block-Cyclic Partitioning): ");
        for (int i = 0; i < N; i++) printf("%d ", C[i]);
        printf("\n");
    }

    MPI_Finalize();
    return 0;
}
```

---

This combines **conceptual explanations** and **array addition examples** for **block**, **cyclic**, and **block-cyclic partitioning**. 
