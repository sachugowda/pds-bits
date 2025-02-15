#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include <sys/resource.h>

#define DATA_SIZE 1000000   // Total data points to process
#define CHUNK_SIZE 100000   // Each slave processes this amount

void process_data(int rank, int data[]) {
    printf("Slave %d processing data...\n", rank);
    for (int i = 0; i < CHUNK_SIZE; i++) {
        data[i] = data[i] * rank;
    }
    printf("Slave %d processing complete.\n", rank);
}

int main(int argc, char** argv) {
    int rank, size;
    int data[CHUNK_SIZE];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int failed_nodes[size - 1];
    memset(failed_nodes, 0, sizeof(failed_nodes));

    if (rank == 0) {
        printf("Master: Distributing work to slaves...\n");
        int full_data[DATA_SIZE];
        for (int i = 0; i < DATA_SIZE; i++) full_data[i] = i;

        for (int i = 1; i < size; i++) {
            MPI_Isend(&full_data[(i - 1) * CHUNK_SIZE], CHUNK_SIZE, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_REQUEST_NULL);
        }

        int received_data[CHUNK_SIZE];
        for (int i = 1; i < size; i++) {
            int flag;
            MPI_Iprobe(i, MPI_ANY_TAG, MPI_COMM_WORLD, &flag, MPI_STATUS_IGNORE);
            if (!flag) {
                failed_nodes[i - 1] = 1;
                printf("Slave %d failed!\n", i);
            } else {
                MPI_Recv(received_data, CHUNK_SIZE, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                printf("Master received data from Slave %d\n", i);
            }
        }

        printf("Master: Data processing completed.\n");

    } else {
        MPI_Recv(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("Slave %d received data, starting processing...\n", rank);
        process_data(rank, data);
        int bytes_sent;
        MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
        printf("Node %d sent %d bytes.\n", rank, bytes_sent);
        MPI_Isend(data, CHUNK_SIZE, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_REQUEST_NULL);
    }

    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    printf("Node %d: CPU usage: %ld sec %ld usec, Memory usage: %ld KB\n", rank, usage.ru_utime.tv_sec, usage.ru_utime.tv_usec, usage.ru_maxrss);

    MPI_Finalize();
    return 0;
}
