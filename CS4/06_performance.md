Simple **serial and parallel bubble sort implementation** in C using **OpenMP** along with a performance comparison (speedup, efficiency, and scalability).

---

### **Serial Bubble Sort (C Code)**

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void bubble_sort_serial(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int n = 10000;
    int arr[n];
    srand(time(0));
    for (int i = 0; i < n; i++)
        arr[i] = rand() % 10000;

    clock_t start = clock();
    bubble_sort_serial(arr, n);
    clock_t end = clock();

    printf("Serial Bubble Sort Time: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);
    return 0;
}
```

---

### **Parallel Bubble Sort (C Code using OpenMP)**

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <omp.h>

void bubble_sort_parallel(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        #pragma omp parallel for
        for (int j = i % 2; j < n - 1; j += 2) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int n = 10000;
    int arr[n];
    srand(time(0));
    for (int i = 0; i < n; i++)
        arr[i] = rand() % 10000;

    double start = omp_get_wtime();
    bubble_sort_parallel(arr, n);
    double end = omp_get_wtime();

    printf("Parallel Bubble Sort Time: %f seconds\n", end - start);
    return 0;
}
```

---

### **Steps for Performance Comparison**

**1. Time Measurement:**
   - Use `clock()` for serial.
   - Use `omp_get_wtime()` for parallel.

**2. Speedup (S):**
   \[
   S = \frac{T_{serial}}{T_{parallel}}
   \]
   Speedup indicates how many times faster the parallel algorithm is compared to the serial one.

**3. Efficiency (E):**
   \[
   E = \frac{S}{p}
   \]
   where `p` is the number of processors (threads). Efficiency measures how well the parallel resources are utilized.

**4. Scalability:**
   - Run the parallel version with different numbers of threads (2, 4, 8, etc.).
   - Measure the runtime and observe the trend in speedup and efficiency.

---

### **Output Example (for different threads)**

| **Threads** | **Serial Time (s)** | **Parallel Time (s)** | **Speedup (S)** | **Efficiency (E)** |
|-------------|----------------------|------------------------|------------------|--------------------|
| 1           | 2.35                 | 2.35                   | 1.00             | 1.00               |
| 2           | 2.35                 | 1.25                   | 1.88             | 0.94               |
| 4           | 2.35                 | 0.68                   | 3.45             | 0.86               |
| 8           | 2.35                 | 0.40                   | 5.87             | 0.73               |

---

### **Observations:**
- **Speedup increases** with the number of threads.
- **Efficiency drops** slightly due to communication and synchronization overhead.
- **Scalability** is evident when performance improves as the number of threads increases, but after a point, diminishing returns are observed.
