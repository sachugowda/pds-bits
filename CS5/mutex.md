
## 1. The Basic Problem

We want multiple threads to safely update some *shared variable* (or shared data structure) without corrupting it. This means we need a **critical section**—a region of code where only **one thread at a time** can be active.

### Why Not Busy-Waiting?
- **Busy-waiting**: A thread sits in a loop checking a condition, consuming CPU time (spinning). This wastes resources if the thread cannot actually do useful work while waiting.
- With a small number of threads (<= number of cores), busy-waiting may not hurt performance much. However, if you have **more threads than cores**, performance can deteriorate because many threads may spin simultaneously without making progress.

---

## 2. What Is a Mutex?

A **mutex** (short for *mutual exclusion*) is a special variable that provides a simple way to **lock** and **unlock** a critical section. 
- If a thread calls `pthread_mutex_lock(&mutex)`, it will **wait** if another thread already has the lock.
- When that other thread calls `pthread_mutex_unlock(&mutex)`, the lock is freed, and **exactly one** waiting thread is allowed to proceed.

With a mutex, threads **block** rather than *spin*. The operating system can reschedule other threads on the CPU instead of burning cycles in a tight loop.

---

## 3. Using a Mutex in Code

Here’s a **simple** code snippet showing how to use a `pthread_mutex_t` for protecting a shared variable `sum`:

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// Global variables
long long n = 100000000;     // Example for a large computation
int thread_count = 4;        // Suppose 4 threads
double sum = 0.0;            // Shared sum
pthread_mutex_t mutex;       // Our global mutex for locking

void* Thread_sum(void* rank) {
    long my_rank = (long) rank;
    long long my_n = n / thread_count;
    long long my_first_i = my_n * my_rank;
    long long my_last_i  = my_first_i + my_n;

    double my_sum = 0.0;   // Thread’s local partial sum

    // 1. Compute partial sum independently
    for (long long i = my_first_i; i < my_last_i; i++) {
        double factor = (i % 2 == 0) ? 1.0 : -1.0;
        my_sum += factor / (2*i + 1);
    }

    // 2. Lock the mutex before updating the global sum
    pthread_mutex_lock(&mutex);

    sum += my_sum; // <-- Critical section: updating shared data

    // 3. Unlock the mutex
    pthread_mutex_unlock(&mutex);

    return NULL;
}

int main(int argc, char* argv[]) {
    pthread_t* thread_handles;
    thread_handles = malloc(thread_count * sizeof(pthread_t));

    // Initialize the mutex (use default attributes)
    pthread_mutex_init(&mutex, NULL);

    // Create threads
    for (long thread = 0; thread < thread_count; thread++) {
        pthread_create(&thread_handles[thread], NULL, Thread_sum, (void*) thread);
    }

    // Wait for threads to finish
    for (int thread = 0; thread < thread_count; thread++) {
        pthread_join(thread_handles[thread], NULL);
    }

    // The global sum has been safely updated by all threads
    printf("Final sum = %f\n", sum);

    // Clean up
    pthread_mutex_destroy(&mutex);
    free(thread_handles);
    return 0;
}
```

### Explanation of the Key Steps

1. **Declare/Initialize Mutex**  
   ```c
   pthread_mutex_t mutex;               // Declare a global mutex
   pthread_mutex_init(&mutex, NULL);    // Initialize it (NULL = default attributes)
   ```
   
2. **Lock Before Critical Section**  
   ```c
   pthread_mutex_lock(&mutex);
   sum += my_sum;    // Critical section: only one thread at a time
   ```
   - If another thread is already inside the critical section, this call blocks until that thread finishes and calls `pthread_mutex_unlock`.

3. **Unlock After Critical Section**  
   ```c
   pthread_mutex_unlock(&mutex);
   ```
   - This signals that the current thread is done updating `sum`. The OS can let another waiting thread acquire the lock.

4. **Destroy Mutex**  
   ```c
   pthread_mutex_destroy(&mutex);
   ```
   - When you’re done (i.e., before program exit or when the mutex is no longer needed), you release any resources used by the mutex.

---

## 4. Why Mutexes Help with More Threads

1. **No Spinning**: Threads that cannot enter the critical section do not keep checking a condition repeatedly. They are put to sleep by the OS and thus **do not** burn CPU cycles.
2. **Better Scaling**: If you have more threads than CPU cores, the OS can schedule different threads or tasks on available cores, rather than letting threads spin.  
3. **Cleaner Semantics**: It’s easy to see where the critical section begins and ends (`mutex_lock`/`mutex_unlock`).

---

## 5. Performance Insights

- With a **small** number of threads (less than or equal to the number of cores), **busy-waiting** might not seem too bad. The waiting thread might get scheduled on a free core and not hamper performance significantly.  
- With **many** threads, mutexes avoid the chaos of many threads spinning. 
- **Lock Contention**: Even with mutexes, if lots of threads try to enter the same critical section frequently, you can still have slowdowns—but it’s still better than busy-waiting in most cases.

---

## 6. Key Takeaways (in Simple Terms)

1. **Mutexes** ensure **only one thread** can access the critical section at a time.  
2. **Lock** the mutex to “enter” the critical section, **unlock** it to “leave.”  
3. **Busy-waiting** wastes CPU cycles by checking in a loop; **mutexes** let the system schedule other threads when a thread can’t enter the critical section immediately.  
4. **Scaling** beyond the number of CPU cores is **much** more efficient with mutexes, which avoid performance collapse due to spinning.

---

Mutexes provide a **cleaner, more efficient** approach than busy-waiting for controlling access to shared data across multiple threads.
