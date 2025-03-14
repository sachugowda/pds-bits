

### **Simple OpenMP Program**
```c
#include <stdio.h>
#include <omp.h>

int main() {
    #pragma omp parallel  // Parallel region starts here
    {
        int thread_id = omp_get_thread_num();  // Get the current thread ID
        printf("Hello from thread %d\n", thread_id);
    }

    return 0;
}
```

---

### **Explanation:**
1. **`#pragma omp parallel`**: This creates multiple threads that execute the enclosed code block in parallel.
2. **`omp_get_thread_num()`**: Retrieves the ID of the thread currently executing.
3. **Output**: Each thread prints a message, but the order may vary due to parallel execution.

---

### **How to Compile and Run in Linux/macOS**
#### **Step 1: Compile using `gcc` (with OpenMP flag)**
```sh
gcc -fopenmp program.c -o program
```
- `-fopenmp`: Enables OpenMP support in `gcc`.
- `program.c`: Your C source file.
- `-o program`: Output executable name.

#### **Step 2: Run the program**
```sh
./program
```

#### **Step 3: Set the number of threads (Optional)**
You can control the number of threads by setting the `OMP_NUM_THREADS` environment variable:
```sh
export OMP_NUM_THREADS=4
./program
```
or modify the program:
```c
#include <stdio.h>
#include <omp.h>

int main() {
    omp_set_num_threads(4);  // Set 4 threads

    #pragma omp parallel
    {
        int thread_id = omp_get_thread_num();
        printf("Hello from thread %d\n", thread_id);
    }

    return 0;
}
```

---

### **Expected Output (Thread Order May Vary)**
```
Hello from thread 1
Hello from thread 2
Hello from thread 0
Hello from thread 3
```
