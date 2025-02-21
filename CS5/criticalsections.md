
---

## 1. What Is a Critical Section?

A **critical section** is a piece of code that **accesses and modifies shared data**. If multiple threads can execute that code at the same time, the data might become inconsistent or produce unpredictable results—a scenario called a **race condition**.

- **Race Condition Example**: Two threads both want to update a shared variable. If Thread A reads the variable and then Thread B reads the variable (before A’s update is stored), one thread’s update may overwrite the other’s. Hence the final value depends on the *timing*, not just the logic.

### Key Point
You must ensure that **only one thread at a time** can execute the critical section that modifies (or sometimes even reads) a shared resource if consistency is at risk. This is usually done with synchronization mechanisms like **mutexes** (mutual exclusion locks).

---

## 2. Example Program Without Protection

Below is a **toy bank account** program. We have:

- A global `balance` (shared resource).  
- Two threads:
  - One **deposits** money (`+500`).  
  - One **pays a bill** (`-100`).  

We want the final balance to be **initial_balance + 400**. However, because we don’t protect the updates, we might get the wrong result.

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// Shared resource: The balance in a bank account
int balance = 1000;

// Thread function #1: Deposit 500
void* deposit(void* arg) {
    // CRITICAL SECTION (UNPROTECTED)
    int temp = balance;     // (1) Read the global balance
    temp = temp + 500;      // (2) Add 500
    balance = temp;         // (3) Write back to global balance

    return NULL;
}

// Thread function #2: Pay a 100 bill
void* payBill(void* arg) {
    // CRITICAL SECTION (UNPROTECTED)
    int temp = balance;     // (1) Read the global balance
    temp = temp - 100;      // (2) Subtract 100
    balance = temp;         // (3) Write back to global balance

    return NULL;
}

int main(void) {
    pthread_t t1, t2;

    printf("Initial balance = %d\n", balance);

    // Create two threads
    pthread_create(&t1, NULL, deposit, NULL);
    pthread_create(&t2, NULL, payBill, NULL);

    // Wait for both threads to finish
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    // In theory, final should be 1000 + 500 - 100 = 1400
    // but sometimes you might see 900, 1500, or 1000 if a race occurs
    printf("Final balance   = %d\n", balance);

    return 0;
}
```

### What Can Go Wrong?

1. **Unpredictable Final Balance**  
   - Sometimes you’ll see `1400` (the correct result).  
   - Other times `900`, `1500`, or even `1000`.  
   - The outcome depends on the timing of reads and writes among the threads.

2. **Why?**  
   - Each of the lines, `balance = balance + 500;` or `balance = balance - 100;`, compiles to multiple instructions:
     1. Read `balance` from memory into a register.  
     2. Add or subtract in that register.  
     3. Write the new value back to memory.  
   - If both threads do these steps **interleaved** in the wrong way, one update overwrites the other’s.

Hence we have discovered the **critical section**: updating the global `balance`. Both threads attempt to do it simultaneously, causing a race condition.

---

## 3. Fixing It with a Mutex (Mutual Exclusion)

To avoid two threads simultaneously updating `balance`, we protect the critical section with a **mutex lock**:

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

int balance = 1000;

// Declare a mutex
pthread_mutex_t balance_mutex;

// Thread #1: Deposit
void* deposit(void* arg) {
    pthread_mutex_lock(&balance_mutex);
    // --- BEGIN CRITICAL SECTION ---
    int temp = balance;
    temp += 500;
    balance = temp;
    // --- END CRITICAL SECTION ---
    pthread_mutex_unlock(&balance_mutex);
    return NULL;
}

// Thread #2: Pay Bill
void* payBill(void* arg) {
    pthread_mutex_lock(&balance_mutex);
    // --- BEGIN CRITICAL SECTION ---
    int temp = balance;
    temp -= 100;
    balance = temp;
    // --- END CRITICAL SECTION ---
    pthread_mutex_unlock(&balance_mutex);
    return NULL;
}

int main(void) {
    pthread_t t1, t2;

    // Initialize the mutex before use
    pthread_mutex_init(&balance_mutex, NULL);

    printf("Initial balance = %d\n", balance);

    // Create threads
    pthread_create(&t1, NULL, deposit, NULL);
    pthread_create(&t2, NULL, payBill, NULL);

    // Join threads
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    // Check final result
    printf("Final balance   = %d\n", balance);

    // Destroy the mutex after use
    pthread_mutex_destroy(&balance_mutex);

    return 0;
}
```

### Explanation

1. **`pthread_mutex_t`**: A special variable that controls exclusive access to a region of code.  
2. **`pthread_mutex_lock()`**: A thread **waits** until it can acquire the lock. Once locked, no other thread can lock it until the first thread unlocks it.  
3. **`pthread_mutex_unlock()`**: The thread **releases** the lock, allowing another thread to proceed.  

With this change, only **one** thread can execute the “read-modify-write” part on `balance` at any given time. This ensures we get the correct final result of 1400.

---

## 4. Why Is This Called a “Critical Section”?

- Any code that **must not be executed by more than one thread at the same time** is a critical section.  
- Typical examples:
  - Updating shared counters or sums  
  - Modifying a shared data structure (like a queue or linked list)  
  - Writing to a shared file or database record

If multiple threads can *concurrently* enter a critical section, we risk **data races** and **inconsistent state**.

---

## 5. Summary

- A **critical section** is a block of code that modifies (or sometimes reads) a shared variable in a way that can lead to inconsistencies if done by multiple threads at once.  
- Without synchronization, threads’ updates can interfere with each other, causing **race conditions**.  
- Mechanisms like **mutex locks** ensure **mutual exclusion**—only one thread can enter the critical section at a time, guaranteeing correct behavior.
