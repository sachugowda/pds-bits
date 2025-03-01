#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include <unistd.h>       // For usleep
#include <pthread.h>      // For multithreading

// ------------------ Configurable Parameters ---------------------
#define DATA_SIZE 1000000
#define CHUNK_SIZE 100000
#define HEARTBEAT_TIMEOUT 5  // seconds

// Number of worker threads per slave node
#define NUM_THREADS 4

// ---------------------------------------------------------------

// Structure for passing work info to each thread
typedef struct {
    int thread_id;
    int rank;
    int* data;
    int start_idx;
    int end_idx;
} ThreadTask;

// Thread function: processes a portion of the data array
void* thread_process(void* arg) {
    ThreadTask* task = (ThreadTask*)arg;
    int rank = task->rank;

    for (int i = task->start_idx; i < task->end_idx; i++) {
        // Simple multiply by rank (as a placeholder for real compute)
        task->data[i] = task->data[i] * rank;
    }

    // Could also return partial stats if needed
    pthread_exit(NULL);
}

// Slave-side function: spawns threads to process the chunk of data in parallel
void process_data_multithreaded(int rank, int data[], int data_size) {
    printf("Slave %d: Spawning %d threads to process data.\n", rank, NUM_THREADS);

    // Create and launch threads
    pthread_t threads[NUM_THREADS];
    ThreadTask tasks[NUM_THREADS];

    int chunk_per_thread = data_size / NUM_THREADS;
    for (int t = 0; t < NUM_THREADS; t++) {
        tasks[t].thread_id = t;
        tasks[t].rank = rank;
        tasks[t].data = data;
        tasks[t].start_idx = t * chunk_per_thread;
        
        // Last thread may go to the end in case data_size % NUM_THREADS != 0
        if (t == NUM_THREADS - 1) {
            tasks[t].end_idx = data_size;
        } else {
            tasks[t].end_idx = (t + 1) * chunk_per_thread;
        }

        pthread_create(&threads[t], NULL, thread_process, &tasks[t]);
    }

    // Wait for all threads to finish
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }

    printf("Slave %d: All threads completed processing.\n", rank);
}

int main(int argc, char** argv) {
    int rank, size;
    // Each slave processes CHUNK_SIZE elements, but we split among threads
    int data[CHUNK_SIZE];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Track node failures
    int failed_nodes[size];
    for (int i = 0; i < size; ++i) {
        failed_nodes[i] = 0; // 0 -> alive, 1 -> failed
    }
    int num_failed_nodes = 0;

    if (rank == 0) {
        // ---------------- Master Node ----------------
        printf("Master: Distributing work to slaves...\n");

        // Full dataset
        int full_data[DATA_SIZE];
        for (int i = 0; i < DATA_SIZE; i++) {
            full_data[i] = i;
        }

        // Distribute initial work to slaves
        int chunk_index = 0;
        for (int i = 1; i < size; i++) {
            if (failed_nodes[i] == 0) {
                // Compress the sub-chunk
                unsigned char compressed_data[CHUNK_SIZE + 100];
                uLongf compressed_size = sizeof(compressed_data);

                compress(compressed_data, &compressed_size,
                         (const Bytef*)&full_data[chunk_index * CHUNK_SIZE],
                         CHUNK_SIZE * sizeof(int)); // note: multiply for bytes

                // Non-blocking send
                MPI_Request request;
                MPI_Isend(compressed_data, compressed_size, MPI_UNSIGNED_CHAR,
                          i, 0, MPI_COMM_WORLD, &request);
                // Wait for send to complete before overwriting buffer
                MPI_Wait(&request, MPI_STATUS_IGNORE);

                chunk_index++;

                // Measure overhead (approximate)
                int bytes_sent;
                MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
                printf("Master: sent ~%d bytes to slave %d.\n", bytes_sent, i);
            }
        }

        // Receive processed data (or detect failures)
        int received_data[CHUNK_SIZE];
        unsigned char received_compressed_data[CHUNK_SIZE + 100];
        MPI_Status status;

        for (int i = 1; i < size; i++) {
            if (failed_nodes[i] == 0) {
                MPI_Request recv_request;
                MPI_Irecv(received_compressed_data, sizeof(received_compressed_data),
                          MPI_UNSIGNED_CHAR, i, 0, MPI_COMM_WORLD, &recv_request);

                // Heartbeat-based timeout
                int flag = 0;
                double start_time = MPI_Wtime();
                while (!flag && (MPI_Wtime() - start_time) < HEARTBEAT_TIMEOUT) {
                    MPI_Test(&recv_request, &flag, &status);
                    usleep(10000); // 10ms
                }

                if (flag) {
                    // Data arrived in time
                    uLongf uncompressed_size = CHUNK_SIZE * sizeof(int);
                    uncompress((Bytef*)received_data, &uncompressed_size,
                               received_compressed_data, status.count);

                    printf("Master: Received processed chunk from slave %d.\n", i);
                } else {
                    // Node is deemed failed
                    failed_nodes[i] = 1;
                    num_failed_nodes++;
                    printf("Slave %d failed! (Heartbeat Timeout)\n", i);

                    MPI_Cancel(&recv_request);
                    MPI_Request_free(&recv_request);
                }
            }
        }

        // If any slaves failed, attempt a simple redistribution
        if (num_failed_nodes > 0) {
            printf("Master: Redistributing workload due to node failures.\n");
            int active_slaves = size - 1 - num_failed_nodes;

            // For simplicity, we’ll just re-send the first chunk(s)
            // In a real system, you'd track unprocessed chunks more carefully
            chunk_index = 0;
            for (int i = 1; i < size; i++) {
                if (failed_nodes[i] == 0) {
                    unsigned char compressed_data[CHUNK_SIZE + 100];
                    uLongf compressed_size = sizeof(compressed_data);

                    compress(compressed_data, &compressed_size,
                             (const Bytef*)&full_data[chunk_index * CHUNK_SIZE],
                             CHUNK_SIZE * sizeof(int));

                    MPI_Request request;
                    MPI_Isend(compressed_data, compressed_size, MPI_UNSIGNED_CHAR,
                              i, 0, MPI_COMM_WORLD, &request);
                    MPI_Wait(&request, MPI_STATUS_IGNORE);

                    chunk_index++;
                    if (chunk_index * CHUNK_SIZE >= DATA_SIZE) break;
                }
            }
        }

        printf("Master: All data processing (and re-distribution if needed) complete.\n");

    } else {
        // ---------------- Slave Nodes ----------------
        // Non-blocking receive from master
        unsigned char compressed_data[CHUNK_SIZE + 100];
        MPI_Status status;

        MPI_Request recv_request;
        MPI_Irecv(compressed_data, sizeof(compressed_data), MPI_UNSIGNED_CHAR,
                  0, 0, MPI_COMM_WORLD, &recv_request);
        MPI_Wait(&recv_request, &status);

        // Decompress
        uLongf uncompressed_size = CHUNK_SIZE * sizeof(int);
        uncompress((Bytef*)data, &uncompressed_size,
                   compressed_data, status.count);

        printf("Slave %d: Received data, starting **multithreaded** processing...\n", rank);

        // Multithreaded processing
        process_data_multithreaded(rank, data, CHUNK_SIZE);

        // Compress the processed data to send back
        unsigned char compressed_data_send[CHUNK_SIZE + 100];
        uLongf compressed_size_send = sizeof(compressed_data_send);

        compress(compressed_data_send, &compressed_size_send,
                 (const Bytef*)data, CHUNK_SIZE * sizeof(int));

        // Send result back to master
        MPI_Request send_request;
        MPI_Isend(compressed_data_send, compressed_size_send, MPI_UNSIGNED_CHAR,
                  0, 0, MPI_COMM_WORLD, &send_request);
        MPI_Wait(&send_request, MPI_STATUS_IGNORE);

        // Approximate overhead
        int bytes_sent;
        MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
        printf("Slave %d: Sent ~%d bytes back to master.\n", rank, bytes_sent);
    }

    MPI_Finalize();
    return 0;
}
