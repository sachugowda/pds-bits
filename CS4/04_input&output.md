# **Handling Input and Output in MPI**

## **1. Introduction to I/O in MPI**
MPI programs often run in parallel across multiple processes. Handling **input and output (I/O)** in MPI can be challenging because:
- **Standard Output (stdout)** is shared across processes, leading to **random ordering** of printed messages.
- **Standard Input (stdin)** is **only accessible to rank 0** in most MPI implementations, meaning **only one process can take user input**.

---

## **2. Handling Output in MPI**
### **Problem with Printing from Multiple Processes**
If multiple MPI processes print to **stdout** using `printf()`, the output order is **unpredictable**. Example:

### **Incorrect Output Example (Random Order)**
```c
#include <stdio.h>
#include <mpi.h>

int main(void) {
    int my_rank, comm_sz;

    MPI_Init(NULL, NULL);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);

    printf("Process %d of %d > Does anyone have a toothpick?\n", my_rank, comm_sz);

    MPI_Finalize();
    return 0;
}
```

### **Example Output (Unordered due to race conditions)**
```
Process 0 of 6 > Does anyone have a toothpick?
Process 1 of 6 > Does anyone have a toothpick?
Process 2 of 6 > Does anyone have a toothpick?
Process 5 of 6 > Does anyone have a toothpick?
Process 3 of 6 > Does anyone have a toothpick?
Process 4 of 6 > Does anyone have a toothpick?
```
- The order **changes on every run** due to processes **competing for stdout access**.

---

### **Solution: Collecting Output at Process 0**
To ensure **ordered output**, each process **sends its message** to **process 0**, which prints them sequentially.

### **Ordered Output Using `MPI_Send` and `MPI_Recv`**
```c
#include <stdio.h>
#include <mpi.h>

int main(void) {
    int my_rank, comm_sz;
    char message[50];
    MPI_Status status;

    MPI_Init(NULL, NULL);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    if (my_rank != 0) {
        // Each process creates its message
        sprintf(message, "Process %d of %d > Does anyone have a toothpick?", my_rank, comm_sz);
        MPI_Send(message, 50, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
    } else {
        // Process 0 prints its own message
        printf("Process %d of %d > Does anyone have a toothpick?\n", my_rank, comm_sz);
        
        // Process 0 receives and prints messages in order
        for (int source = 1; source < comm_sz; source++) {
            MPI_Recv(message, 50, MPI_CHAR, source, 0, MPI_COMM_WORLD, &status);
            printf("%s\n", message);
        }
    }

    MPI_Finalize();
    return 0;
}
```

### **Expected Ordered Output**
```
Process 0 of 6 > Does anyone have a toothpick?
Process 1 of 6 > Does anyone have a toothpick?
Process 2 of 6 > Does anyone have a toothpick?
Process 3 of 6 > Does anyone have a toothpick?
Process 4 of 6 > Does anyone have a toothpick?
Process 5 of 6 > Does anyone have a toothpick?
```
✅ **Process 0 controls the output order by collecting and printing messages sequentially.**

---

## **3. Handling Input in MPI**
### **Problem: Only Rank 0 Has Access to stdin**
By default, **only process 0** can read user input using `scanf()` because:
- Allowing multiple processes to read from `stdin` would cause **conflicts**.
- No automatic mechanism exists to divide input among processes.

### **Solution: Rank 0 Reads Input and Broadcasts It**
To ensure all processes have access to the same input values, **process 0 reads input**, then **sends** it to other processes.

### **Using `MPI_Send` and `MPI_Recv` for Input Distribution**
```c
#include <stdio.h>
#include <mpi.h>

void Get_input(int my_rank, int comm_sz, double* a, double* b, int* n) {
    if (my_rank == 0) {
        // Rank 0 gets user input
        printf("Enter a, b, and n: ");
        scanf("%lf %lf %d", a, b, n);

        // Rank 0 sends input to all other processes
        for (int dest = 1; dest < comm_sz; dest++) {
            MPI_Send(a, 1, MPI_DOUBLE, dest, 0, MPI_COMM_WORLD);
            MPI_Send(b, 1, MPI_DOUBLE, dest, 0, MPI_COMM_WORLD);
            MPI_Send(n, 1, MPI_INT, dest, 0, MPI_COMM_WORLD);
        }
    } else {
        // Other processes receive input from Rank 0
        MPI_Recv(a, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(b, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(n, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
}

int main(int argc, char* argv[]) {
    int my_rank, comm_sz;
    double a, b;
    int n;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    Get_input(my_rank, comm_sz, &a, &b, &n);

    // Each process prints received input
    printf("Process %d received a=%.2f, b=%.2f, n=%d\n", my_rank, a, b, n);

    MPI_Finalize();
    return 0;
}
```

---

### **Expected Behavior**
#### **User Input (Entered by Rank 0)**
```
Enter a, b, and n:
0.0 3.0 1024
```

#### **Output on All Processes**
```
Process 0 received a=0.00, b=3.00, n=1024
Process 1 received a=0.00, b=3.00, n=1024
Process 2 received a=0.00, b=3.00, n=1024
Process 3 received a=0.00, b=3.00, n=1024
```
✅ **All processes now have the same input values!**

---

## **4. Alternative: Using `MPI_Bcast` for Input Distribution**
Instead of multiple `MPI_Send` calls, we can use `MPI_Bcast`, which **broadcasts data** from Rank 0 to all processes **in one step**.

```c
void Get_input(int my_rank, double* a, double* b, int* n) {
    if (my_rank == 0) {
        printf("Enter a, b, and n: ");
        scanf("%lf %lf %d", a, b, n);
    }

    // Broadcast input values to all processes
    MPI_Bcast(a, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(b, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(n, 1, MPI_INT, 0, MPI_COMM_WORLD);
}
```

✅ **`MPI_Bcast` is more efficient than multiple `MPI_Send` calls!**

---

## **5. Summary**
| **Operation**  | **Problem** | **Solution** |
|--------------|------------|------------|
| **Output (stdout)** | Random ordering of messages | Send messages to **process 0** for ordered printing |
| **Input (stdin)** | Only Rank 0 can read input | Rank 0 reads input and **distributes** it using `MPI_Send` or `MPI_Bcast` |
| **Efficient Broadcast** | Multiple `MPI_Send` calls are inefficient | Use `MPI_Bcast` to **broadcast input to all processes** |

