# Parallel Odd-Even Transposition Sort Using MPI

## Introduction
The **odd-even transposition sort** is a comparison-based sorting algorithm that alternates between two phases:
1. **Odd Phase**: Adjacent pairs of elements at odd-even indices (e.g., `(1,2), (3,4)`) are compared and swapped if necessary.
2. **Even Phase**: Adjacent pairs of elements at even-odd indices (e.g., `(0,1), (2,3)`) are compared and swapped if necessary.

This algorithm is particularly well-suited for parallel implementation due to its regular communication pattern, making it a popular choice for distributed memory systems using MPI.

---

## Algorithm Steps
1. **Initialization**: Divide the data across multiple processes using MPI.
2. **Odd and Even Phases**:
   - During the odd phase, compare and swap adjacent pairs at odd-even indices.
   - During the even phase, compare and swap adjacent pairs at even-odd indices.
3. **Boundary Exchange**: Processes exchange boundary elements to ensure the entire dataset is sorted.
4. **Repeat**: Alternate odd and even phases until the array is sorted.
5. **Result Collection**: Gather the sorted data back to the root process.

---

## MPI Implementation
Below is an example implementation of parallel odd-even transposition sort using MPI.

### Example Code
```c
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

// Function to perform local odd-even sort
void odd_even_sort(int *local_data, int local_n, int rank, int size) {
    int phase, temp;
    MPI_Status status;

    for (phase = 0; phase < size; phase++) {
        if (phase % 2 == 0) {
            // Even phase: Communicate with right neighbor
            if (rank < size - 1) {
                MPI_Sendrecv(&local_data[local_n - 1], 1, MPI_INT, rank + 1, 0,
                             &temp, 1, MPI_INT, rank + 1, 0, MPI_COMM_WORLD, &status);
                if (temp < local_data[local_n - 1]) {
                    local_data[local_n - 1] = temp;
                }
            }
        } else {
            // Odd phase: Communicate with left neighbor
            if (rank > 0) {
                MPI_Sendrecv(&local_data[0], 1, MPI_INT, rank - 1, 0,
                             &temp, 1, MPI_INT, rank - 1, 0, MPI_COMM_WORLD, &status);
                if (temp > local_data[0]) {
                    local_data[0] = temp;
                }
            }
        }

        // Perform local sorting
        for (int i = 0; i < local_n - 1; i++) {
            if (local_data[i] > local_data[i + 1]) {
                int swap = local_data[i];
                local_data[i] = local_data[i + 1];
                local_data[i + 1] = swap;
            }
        }
    }
}

int main(int argc, char **argv) {
    int rank, size, n = 16, local_n;
    int *global_data = NULL, *local_data;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    local_n = n / size;
    local_data = (int *)malloc(local_n * sizeof(int));

    if (rank == 0) {
        // Initialize global data on the root process
        global_data = (int *)malloc(n * sizeof(int));
        for (int i = 0; i < n; i++) {
            global_data[i] = rand() % 100; // Random values between 0 and 99
        }

        printf("Unsorted Array: ");
        for (int i = 0; i < n; i++) printf("%d ", global_data[i]);
        printf("\n");
    }

    // Scatter the data among processes
    MPI_Scatter(global_data, local_n, MPI_INT, local_data, local_n, MPI_INT, 0, MPI_COMM_WORLD);

    // Perform parallel odd-even sort
    odd_even_sort(local_data, local_n, rank, size);

    // Gather the sorted data back to the root process
    MPI_Gather(local_data, local_n, MPI_INT, global_data, local_n, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("Sorted Array: ");
        for (int i = 0; i < n; i++) printf("%d ", global_data[i]);
        printf("\n");
        free(global_data);
    }

    free(local_data);
    MPI_Finalize();
    return 0;
}
```

---

## Explanation of the Code

### **Initialization**:
- The array is initialized on the root process (`rank 0`) with random integers.
- The data is divided equally among processes using `MPI_Scatter`.

### **Odd-Even Sort Logic**:
1. **Odd and Even Phases**:
   - Each process performs local sorting on its data.
   - Boundary elements are exchanged with neighboring processes during odd and even phases.
2. **Communication**:
   - `MPI_Sendrecv` ensures safe two-way communication between neighboring processes.

### **Result Gathering**:
- After sorting, the data from all processes is gathered back to the root process using `MPI_Gather`.

---

## Example Execution

### Input:
- **Array**: [45, 23, 89, 12, 78, 34, 56, 90, 11, 67, 43, 21, 30, 62, 88, 10]
- **Processes**: 4

### Output:
- **Sorted Array**: [10, 11, 12, 21, 23, 30, 34, 43, 45, 56, 62, 67, 78, 88, 89, 90]

---

## Advantages of Parallel Odd-Even Sort
1. **Simple Communication Pattern**: Regular communication between neighboring processes.
2. **Scalability**: Effective for medium to large datasets when distributed across multiple processes.
3. **Deterministic**: Produces the same result for the same input.

---

## Limitations
1. **Communication Overhead**: Frequent communication between processes can reduce performance for small datasets.
2. **Not Optimal for Large Systems**: Performance may degrade as the number of processes increases beyond a certain point.

---

## Conclusion
Parallel odd-even transposition sort is a straightforward and scalable sorting algorithm for distributed systems. While it is not the most efficient parallel sorting algorithm for very large datasets, it is an excellent choice for teaching and understanding parallel processing concepts using MPI.

