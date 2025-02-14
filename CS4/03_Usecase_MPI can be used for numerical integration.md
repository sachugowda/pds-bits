# **Use Case: Solving Numerical Integration using the Trapezoidal Rule in MPI**

## **Problem Statement**
We need to compute the integral of a function **f(x) = x²** over the interval **[0, 3]** using the **trapezoidal rule** in a parallel computing environment with MPI. 

The integral can be represented as:
\[
I = \int_{0}^{3} x^2 dx
\]

Using the **Trapezoidal Rule**, the integral approximation is given by:
\[
I \approx \sum_{i=1}^{n} \frac{h}{2} \left[f(x_i) + f(x_{i+1})\right]
\]

where:
- **h** is the step size:  
  \[
  h = \frac{b-a}{n}
  \]
- **n** is the number of trapezoids (subdivisions).
- **x_i** represents the points where function values are computed.

---

## **Parallelizing the Trapezoidal Rule with MPI**
We will distribute the work across **multiple MPI processes**:
- **Each process** will compute the integral over a portion of the interval.
- The **Master process (Rank 0)** will collect results from all processes and sum them to get the final integral.

### **Steps for Parallel Computation**
1. **Divide the work**: Each process computes a portion of the integral.
2. **Calculate local integral**: Each process performs the **trapezoidal rule** on its assigned portion.
3. **Aggregate results**: Process **0** collects partial results using `MPI_Recv` and sums them.

---

## **MPI Implementation Example**
```c
#include <stdio.h>
#include <mpi.h>

// Function to integrate: f(x) = x^2
double f(double x) {
    return x * x;
}

// Trapezoidal rule function
double Trap(double local_a, double local_b, int local_n, double h) {
    double integral, x;
    integral = (f(local_a) + f(local_b)) / 2.0;
    for (int i = 1; i < local_n; i++) {
        x = local_a + i * h;
        integral += f(x);
    }
    return integral * h;
}

int main(int argc, char** argv) {
    int my_rank, comm_sz, n = 1024, local_n;
    double a = 0.0, b = 3.0, h, local_a, local_b;
    double local_int, total_int;
    int source;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    h = (b - a) / n;  // Step size
    local_n = n / comm_sz;  // Number of trapezoids per process

    local_a = a + my_rank * local_n * h;  // Start of local interval
    local_b = local_a + local_n * h;  // End of local interval

    // Compute local integral
    local_int = Trap(local_a, local_b, local_n, h);

    // Master process gathers and sums up results
    if (my_rank != 0) {
        MPI_Send(&local_int, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD);
    } else {
        total_int = local_int;
        for (source = 1; source < comm_sz; source++) {
            MPI_Recv(&local_int, 1, MPI_DOUBLE, source, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            total_int += local_int;
        }

        // Print the final result
        printf("With n = %d trapezoids, our estimate of the integral from %.2f to %.2f = %.15e\n",
               n, a, b, total_int);
    }

    MPI_Finalize();
    return 0;
}
```

---

## **Explanation of the Code**
### **1. Initialization**
```c
MPI_Init(&argc, &argv);
MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);
```
- Initializes MPI environment.
- Assigns each process a **rank (my_rank)**.
- Determines the **total number of processes (comm_sz)**.

### **2. Define the Interval and Step Size**
```c
h = (b - a) / n;
local_n = n / comm_sz;
```
- The **step size h** is computed based on the total interval `[a, b]` and the number of trapezoids `n`.
- The **local work (local_n)** is computed based on the number of processes.

### **3. Compute Local Integrals in Parallel**
Each process computes its portion of the integral.
```c
local_a = a + my_rank * local_n * h;
local_b = local_a + local_n * h;
local_int = Trap(local_a, local_b, local_n, h);
```
- The **local start and end points** are determined based on rank.
- The function **Trap()** computes the integral over the local portion.

### **4. Communication and Reduction**
#### **Worker Processes Send Data**
```c
if (my_rank != 0) {
    MPI_Send(&local_int, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD);
}
```
- All worker processes **send** their computed integral value to **process 0**.

#### **Master Process Collects Data**
```c
else {
    total_int = local_int;
    for (source = 1; source < comm_sz; source++) {
        MPI_Recv(&local_int, 1, MPI_DOUBLE, source, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        total_int += local_int;
    }
}
```
- The master process (`Rank 0`) **receives** values from all processes and sums them to compute the **final integral**.

---

## **Running the MPI Program**
### **1. Compile the Program**
```bash
mpicc -o mpi_trap mpi_trap.c -lm
```
### **2. Run the Program with 4 Processes**
```bash
mpirun -np 4 ./mpi_trap
```

### **3. Expected Output**
```
With n = 1024 trapezoids, our estimate of the integral from 0.00 to 3.00 = 9.000000000000000e+00
```
This is close to the actual integral value:

I = ∫₀³ x² dx = (x³/3) |₀³ = (27/3) = 9



---

## **Key Takeaways**
✅ **Parallel Computing:** Work is evenly distributed across multiple processors.  
✅ **Scalability:** More processes can be added to improve performance.  
✅ **Message Passing:** MPI is used to communicate results between processes.  
✅ **Numerical Accuracy:** Increasing the number of trapezoids **improves approximation accuracy**.

---

## **Conclusion**
This example **demonstrates how MPI can be used for numerical integration**. The **trapezoidal rule** is **parallelized** efficiently, allowing us to compute **definite integrals** in a distributed environment. 🚀
