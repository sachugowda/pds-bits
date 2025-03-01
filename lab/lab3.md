Below is a **step-by-step** guide for **Lab 3**, where you build on the previous **distributed data processing** (Lab 2) by introducing **multithreading** within each slave node. The goal is to exploit multiple CPU cores on a single node for faster local processing and to demonstrate common synchronization issues and solutions.

---

## 1. Overview

**Lab 2 Recap**:  
- You have a **master** node that partitions input data and distributes it across multiple **slave** nodes via **OpenMPI**.  
- Each slave processes its assigned subset of data and returns partial results to the master.  
- The master merges (“reduces”) these partial results and reports final output to the user.  
- You also handle node crashes, compress data to reduce network overhead, track performance metrics, etc.

**New in Lab 3**:  
- Within each **slave** node, use **multithreading** to parallelize the data processing.  
- Each slave now spawns multiple threads (e.g., using **pthreads**) to process its subset of data in smaller chunks concurrently.  
- You need to address **synchronization** to avoid race conditions on shared data structures (e.g., partial results, aggregated metrics).  

---

## 2. Prerequisites

1. A working **Lab 2** codebase (distributed data processing with MPI).  
2. Familiarity with **C/C++** threading libraries (pthreads).  
3. A basic understanding of **mutexes** (or other synchronization primitives).  
4. A multi-core environment so each slave node can actually benefit from threads.

---

## 3. High-Level Architecture

1. **Master** (MPI Rank 0):  
   - Same as in Lab 2.  
   - Receives input data from the user, partitions it, and distributes partitions to the slaves.  
   - Collects partial results (plus any intermediate progress or error reports) from the slaves.  
   - Merges these results into a final output.

2. **Slave** (MPI Rank 1, 2, …):  
   - Receives its partition of data from the master (optionally compressed).  
   - **NEW**: Instead of processing this data in a single thread, it spawns multiple worker threads on the same node.  
   - Each worker thread processes a chunk of the slave’s data.  
   - The slave aggregates the results from its threads, and sends that partial output back to the master.  
   - If the master queries for status or performance, the slave gathers info from each thread (e.g., CPU usage, progress) and returns it.

---

## 4. Implementation Steps

### 4.1 Create a Thread Pool or Spawn Threads Dynamically

**Option A**: Thread Pool  
- On each slave, create a fixed **thread pool** once at the start of the process.  
- Assign data chunks to idle threads from a task queue.

**Option B**: Dynamic Thread Creation  
- For each new dataset partition, spawn threads on demand, then join them after processing completes.

Most labs go with Option B for simplicity. For large, repeated tasks, a pool is more efficient.

### 4.2 Partition Data on Slave Nodes

When a slave receives data from the master, it can further split its subset into smaller chunks—one per thread. For example, if a slave node has 4 CPU cores and each core is to run one thread:

```c
// Suppose 'data' is the slave’s chunk from the master
// Partition size for each thread
int totalSize = ...; // e.g., number of elements
int numThreads = 4;
int chunkSize = totalSize / numThreads;
```

Each thread processes `[startIndex, endIndex]` in the local data.

### 4.3 Multithreaded Processing Function

Create a thread function (pthreads example shown):

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int threadId;
    int* data;
    int start;
    int end;
    // Possibly other fields for results
} ThreadTask;

// Thread function
void* process_data(void* arg) {
    ThreadTask* task = (ThreadTask*)arg;
    int sum = 0;
    for (int i = task->start; i < task->end; i++) {
        // Example: sum up values
        sum += task->data[i];
    }
    // Return the sum as this thread’s partial result
    int* result = malloc(sizeof(int));
    *result = sum;
    pthread_exit(result);
}
```

Your actual computation will vary depending on the lab’s focus (e.g., data analytics, transformations, encryption/decryption).

### 4.4 Synchronizing Partial Results

If each thread returns a local result (e.g., sum, count, or intermediate structure), the slave must **combine** those partial results. You can do it in two ways:

1. **Thread Return Values**: Each thread returns a pointer to its partial result. The main (slave) thread collects them via `pthread_join()`.  
2. **Shared Global**: All threads write into a shared array or structure, protected by a **mutex** or **atomic** operations to avoid race conditions.

**Example** (Collecting thread-returned sums):
```c
int totalSum = 0;
for (int i = 0; i < numThreads; i++) {
    void* threadRetVal;
    pthread_join(thread[i], &threadRetVal);
    int partSum = *(int*)threadRetVal;
    free(threadRetVal);  // free allocated result
    totalSum += partSum;
}
```

### 4.5 Handling Synchronization Problems

- **Race Conditions**: If threads share data (beyond read-only), protect writes with a **mutex** or use atomic operations.  
- **Deadlocks**: Keep locking minimal and consistent. Acquire and release locks in a well-defined order.  
- **False Sharing**: If each thread writes to adjacent memory locations, you might see performance degradation. Try aligning data structures or spacing them out.

### 4.6 Integrating Back with MPI

1. **Master** -> **Slave**: No change in how data is delivered, except the data chunk might be bigger since each slave now handles more local parallelism.  
2. **Slave** does the following:
   - Receives the chunk.  
   - Spawns threads (or uses a thread pool).  
   - Each thread processes part of the chunk.  
   - The slave aggregates those results.  
   - The slave sends aggregated results to the master (MPI send).  
3. **Master** collects partial results from all slaves and performs the final reduce step.

### 4.7 Performance Metrics & Status

- Slaves can track **thread-level** CPU/memory usage if needed, or approximate it.  
- The master can poll slaves for progress, which might be an aggregate of each thread’s progress (e.g., “Thread 0 is 80% done with its chunk, Thread 1 is 60%,” etc.).  
- A simple approach: each thread periodically updates a shared “progress counter,” which the slave sums up to compute an overall fraction complete.

### 4.8 Node Crash + Multithreading

- If a **node** (slave) crashes entirely, the master’s **heartbeat** detection remains the same (no difference from Lab 2).  
- If an **individual thread** crashes on a healthy node, the OS typically kills the entire process (depending on your environment). In that case, from the master’s perspective, it’s again a node crash.  
- If you want more advanced per-thread fault tolerance, that would require more complex error handling within the slave process.

---

## 5. Step-by-Step Execution Tutorial

1. **Set Up MPI**:  
   - Same instructions as Lab 2 for configuring your cluster (hosts file, SSH keys, etc.).  
2. **Install Dependencies**:  
   - If not already installed, ensure you have a **pthreads** or **C++** threading environment, along with any libraries (like **zlib** for compression).  
3. **Code Changes**:  
   - Update your **slave** program’s processing function to spawn threads and combine partial results.  
   - Ensure that any shared data among threads is protected by a mutex or is read-only.  
4. **Compile**:  
   ```bash
   mpicc -o lab3_master master_code.c
   mpicc -o lab3_slave slave_code.c -lpthread
   ```
   Or use a Makefile with the appropriate flags.  
5. **Launch the Cluster**:  
   - If you have an `mpirun` hostfile set up, run:
     ```bash
     mpirun -np 1 --host masterHost ./lab3_master : -np (N) --host slaveHost1,slaveHost2,... ./lab3_slave
     ```
   - Master’s rank is 0. Slaves are ranks 1, 2, …, N.  
6. **Observe Output**:  
   - The master should show distribution of data and final reduced result.  
   - Each slave might print logs about spawning threads, partial results, errors, or performance metrics.  
7. **Test Failure** (optional):  
   - Simulate a slave crash (kill a slave process).  
   - Confirm the master detects it, reassigns tasks if that’s your design (or restarts the job).  
8. **Performance Measurement**:  
   - Time the entire job with different thread counts (e.g., 1, 2, 4, etc.) on each slave.  
   - Compare against Lab 2 baseline performance. You should see improvement on multi-core machines.

---

## 6. Common Pitfalls & Tips

1. **Oversubscription**: Don’t spawn more threads than CPU cores if your workload is purely CPU-bound. This can lead to context-switch overhead outweighing any parallel gains.  
2. **Chunk Size**: Try to balance data among threads so each finishes around the same time.  
3. **Locking Overhead**: Keep your critical sections small. Use local variables inside each thread as much as possible, combining results at the end rather than writing to a shared structure in every iteration.

---

## 7. Conclusion

**Lab 3** extends the distributed solution from Lab 2 by adding local parallelism on each slave node. The major steps are:

1. **Partition** slave data further among threads.  
2. **Spawn** threads to process in parallel.  
3. **Synchronize** partial results to avoid race conditions.  
4. **Return** aggregated results to the master as before.  

This demonstrates how **hybrid parallelism**—MPI across nodes plus multithreading on each node—can significantly speed up large-scale data processing, while requiring careful attention to concurrency issues.
