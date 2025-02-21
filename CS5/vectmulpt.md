# Matrix-vector multiplication

**step-by-step tutorial** on how to write a **Pthreads** program that multiplies a matrix    A (size 𝑚×𝑛) by a vector **x** (size \(n\)). The result is a vector **y** (size \(m\)). We’ll divide the rows of **A** among different threads, so each thread computes part of the result **y**.  

---

## Overview of the Computation

Recall that the product of a matrix \(A\) and a vector \(x\), denoted \(y = A x\), is calculated as follows:


$y_i = \sum_{j=0}^{n-1} A_{ij} \times x_j \quad \text{for each row } i \in \{0, 1, \ldots, m-1\}$.


In **serial** code, we might do:

```c
for (i = 0; i < m; i++) {
    y[i] = 0.0;
    for (j = 0; j < n; j++) {
        y[i] += A[i][j] * x[j];
    }
}
```

To **parallelize**, we’ll split the `i` loop among multiple threads.

---

## Full Example Code: `pth_mat_vect.c`

Below is a simplified, self-contained C program that does the following:

1. Reads **m**, **n**, and **thread_count** from the command line.  
2. Allocates and initializes the matrix **A** and the vector **x** with dummy values (for simplicity).  
3. Creates threads, each of which computes a consecutive “chunk” of rows of **A**.  
4. Collects (joins) the thread results into a shared array **y**.  
5. Prints out the resulting **y**.

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// -------------------------------------------------------------------------
// 1) Global variables: these will be shared among all threads
// -------------------------------------------------------------------------
int     m, n, thread_count; // matrix dimensions and number of threads
double *x;                  // pointer to the vector x
double *y;                  // pointer to the result vector y
double **A;                 // pointer to the 2D matrix A (size m x n)

// -------------------------------------------------------------------------
// 2) Thread function prototype
//    Each thread will compute a chunk of rows for the product y = A*x.
// -------------------------------------------------------------------------
void* Pth_mat_vect(void* rank);

// -------------------------------------------------------------------------
// 3) Main function
// -------------------------------------------------------------------------
int main(int argc, char* argv[]) {
    long    thread;               // Will use 'long' for thread IDs
    pthread_t* thread_handles;    // To store each thread's info
    int i, j;

    // ---------------------------------------------------------------------
    // 3.1) Read command line args: program expects ./a.out <m> <n> <thread_count>
    // ---------------------------------------------------------------------
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <m> <n> <thread_count>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    m = strtol(argv[1], NULL, 10);
    n = strtol(argv[2], NULL, 10);
    thread_count = strtol(argv[3], NULL, 10);

    if (m <= 0 || n <= 0 || thread_count <= 0) {
        fprintf(stderr, "Error: all arguments must be positive.\n");
        exit(EXIT_FAILURE);
    }

    // ---------------------------------------------------------------------
    // 3.2) Allocate memory for A, x, y
    // ---------------------------------------------------------------------
    // A is a 2D matrix, but we can allocate it row by row
    A = malloc(m * sizeof(double*));
    for (i = 0; i < m; i++) {
        A[i] = malloc(n * sizeof(double));
    }

    x = malloc(n * sizeof(double));
    y = malloc(m * sizeof(double));

    // ---------------------------------------------------------------------
    // 3.3) Initialize A and x with some dummy values
    //      (in a real program, you'd read from file or user input)
    // ---------------------------------------------------------------------
    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++) {
            A[i][j] = i + j;  // simple function of i, j
        }
    }
    for (j = 0; j < n; j++) {
        x[j] = 1.0; // just set every element to 1
    }

    // Initialize y to 0
    for (i = 0; i < m; i++) {
        y[i] = 0.0;
    }

    // ---------------------------------------------------------------------
    // 3.4) Create array of threads, then start them
    // ---------------------------------------------------------------------
    thread_handles = malloc(thread_count * sizeof(pthread_t));

    for (thread = 0; thread < thread_count; thread++) {
        pthread_create(&thread_handles[thread],
                       NULL,            // default thread attributes
                       Pth_mat_vect,    // function each thread will run
                       (void*) thread   // pass thread ID as argument
        );
    }

    // ---------------------------------------------------------------------
    // 3.5) Join (wait) for each thread to finish
    // ---------------------------------------------------------------------
    for (thread = 0; thread < thread_count; thread++) {
        pthread_join(thread_handles[thread], NULL);
    }

    // ---------------------------------------------------------------------
    // 3.6) Print the result vector y (optional)
    // ---------------------------------------------------------------------
    printf("Result vector y:\n");
    for (i = 0; i < m; i++) {
        printf("y[%d] = %.2f\n", i, y[i]);
    }

    // ---------------------------------------------------------------------
    // 3.7) Free allocated memory
    // ---------------------------------------------------------------------
    free(thread_handles);
    for (i = 0; i < m; i++) {
        free(A[i]);
    }
    free(A);
    free(x);
    free(y);

    return 0;
} // end main

// -------------------------------------------------------------------------
// 4) Thread function: each thread computes part of y = A*x
//    rank is the thread ID (0, 1, 2, ...).
// -------------------------------------------------------------------------
void* Pth_mat_vect(void* rank) {
    long my_rank       = (long) rank;
    int  i, j;
    // Number of rows each thread handles:
    int  local_m       = m / thread_count;
    // Starting row:
    int  my_first_row  = my_rank * local_m;
    // Ending row:
    int  my_last_row   = (my_rank + 1)*local_m - 1;

    for (i = my_first_row; i <= my_last_row; i++) {
        // We'll accumulate a dot product for row i:
        double temp = 0.0;
        for (j = 0; j < n; j++) {
            temp += A[i][j] * x[j];
        }
        y[i] = temp;  // store the result in the shared y
    }

    return NULL;
}
```

---

## How It Works (Step by Step)

1. **Global Variables**  
   We keep `A`, `x`, `y`, `m`, `n`, and `thread_count` as globals to ensure that every thread sees the same memory space.  
   - `A` is an `m x n` matrix (allocated row-by-row).  
   - `x` is a vector of length `n`.  
   - `y` is a vector of length `m` for the result.

2. **Command-Line Arguments**  
   We expect three numbers:  
   - `m` (number of rows in A / length of y)  
   - `n` (number of columns in A / length of x)  
   - `thread_count` (how many threads we want).

3. **Allocation and Initialization**  
   - We `malloc` space for `A`, `x`, and `y`.  
   - We fill `A` with a simple pattern (`A[i][j] = i + j`) and set every `x[j]` to 1.0. (In practice, you might load from file or read user input.)

4. **Creating Threads**  
   - We create `thread_count` threads, each running `Pth_mat_vect`.  
   - We pass the loop index `thread` as an argument (typecast to `void*`).

5. **Division of Rows**  
   - If `m` is 6 and `thread_count` is 3, each thread gets `local_m = 6 / 3 = 2` rows.  
   - Thread 0: rows 0 to 1  
   - Thread 1: rows 2 to 3  
   - Thread 2: rows 4 to 5  

6. **Computing y[i] in the Thread**  
   - Each thread does a double loop:  
     ```c
     for (i = my_first_row; i <= my_last_row; i++) {
         double temp = 0.0;
         for (j = 0; j < n; j++) {
             temp += A[i][j] * x[j];
         }
         y[i] = temp;
     }
     ```  
   - This multiplies the assigned rows in `A` by the entire vector `x`.  
   - The result is stored in the shared `y`, at positions `[my_first_row ... my_last_row]`.

7. **Joining Threads**  
   - `pthread_join` ensures the main thread waits until all threads have finished before printing the result.

8. **Output**  
   - Finally, we display the resulting `y[i]`.  
   - Each element should be the correct dot product of row `i` of `A` with the vector `x`.

9. **Cleanup**  
   - Always remember to `free` everything you `malloc`.

---

## Example Run

1. **Compile**:
   ```bash
   gcc -o pth_mat_vect pth_mat_vect.c -lpthread
   ```

2. **Run** (example):
   ```bash
   ./pth_mat_vect 6 4 3
   ```
   - `m = 6`, `n = 4`, `thread_count = 3`.

3. **Sample Output**:
   ```
   Result vector y:
   y[0] = 6.00
   y[1] = 10.00
   y[2] = 14.00
   y[3] = 18.00
   y[4] = 22.00
   y[5] = 26.00
   ```
   (These values reflect the sum of row `i` + 1.0 across the columns, with the dummy initialization.)

---

## Key Takeaways

- **Shared Memory**: Threads can all access the same `A`, `x`, and `y` without special message passing.  
- **Data Partitioning**: We split the `i` loop among threads by assigning consecutive row chunks.  
- **Synchronization**: We rely on `pthread_join` to ensure the main thread doesn’t exit before all worker threads are done.  
- **Scalability**: If `m` and `n` are large, parallelizing can lead to significant speedups on multicore systems.

This example shows that **shared-memory parallelism** can be straightforward for tasks like matrix-vector multiplication. Just be mindful of how you divide the data and be sure each thread knows which portion to handle.
