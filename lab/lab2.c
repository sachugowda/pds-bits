#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include <unistd.h> // For sleep

#define DATA_SIZE 1000000
#define CHUNK_SIZE 100000
#define HEARTBEAT_TIMEOUT 5  // seconds

// Function to simulate data processing at slave nodes
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

    //4. Handling Node Failures
    int failed_nodes[size]; // Use a dynamic size array to store failure status
    for (int i = 0; i < size; ++i) {
        failed_nodes[i] = 0; // Initialize all nodes as not failed
    }
    int num_failed_nodes = 0; // Track number of failed nodes.

    if (rank == 0) { // Master Node
        printf("Master: Distributing work to slaves...\n");

        int full_data[DATA_SIZE];
        for (int i = 0; i < DATA_SIZE; i++) full_data[i] = i;

        // Distribute work to slaves (initially)
        int chunk_index = 0;
        for (int i = 1; i < size; i++) {
            if(failed_nodes[i] == 0) //Only send to non failed nodes
            {
                // 5.1 Using Non-Blocking Send/Receive + 5.2 Data Compression
                unsigned char compressed_data[CHUNK_SIZE + 100]; // Add extra space for potential compression expansion
                uLongf compressed_size = sizeof(compressed_data); // Size of dest buffer
                compress(compressed_data, &compressed_size, (const Bytef *)&full_data[chunk_index * CHUNK_SIZE], CHUNK_SIZE);

                MPI_Request request;
                MPI_Isend(compressed_data, compressed_size, MPI_UNSIGNED_CHAR, i, 0, MPI_COMM_WORLD, &request);
                MPI_Wait(&request, MPI_STATUS_IGNORE); // Wait for send to complete.
                chunk_index++;

                // 6.2 Measure Communication Overhead (on sender)
                int bytes_sent;
                MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
                printf("Master Node %d sent %d bytes to node %d.\n", rank, bytes_sent, i);
            }
        }

        // Receive processed data from slaves and check for failures
        int received_data[CHUNK_SIZE];
        unsigned char received_compressed_data[CHUNK_SIZE + 100];
        MPI_Status status;

        for (int i = 1; i < size; i++) {
            if (failed_nodes[i] == 0) // Only receive from non-failed nodes
            {
                MPI_Request recv_request;

                // Start non-blocking receive
                MPI_Irecv(received_compressed_data, sizeof(received_compressed_data), MPI_UNSIGNED_CHAR, i, 0, MPI_COMM_WORLD, &recv_request);

                // Heartbeat Check (modified)
                int flag = 0;
                double start_time = MPI_Wtime();
                while (flag == 0 && (MPI_Wtime() - start_time) < HEARTBEAT_TIMEOUT) {
                    MPI_Test(&recv_request, &flag, &status); // Check if data is received
                    usleep(10000);                                // Sleep for 10 milliseconds to avoid busy-waiting
                }

                if (flag) {
                    uLongf uncompressed_size = CHUNK_SIZE;
                    uncompress((Bytef *)received_data, &uncompressed_size, received_compressed_data, status.count);

                    printf("Master received data from Slave %d\n", i);
                } else {
                    failed_nodes[i] = 1;
                    num_failed_nodes++;
                    printf("Slave %d failed! (Heartbeat Timeout)\n", i);
                    MPI_Cancel(&recv_request); // Cancel the pending receive
                    MPI_Request_free(&recv_request); // Free the request object
                }
            }

        }

        //Redistribute work to remaining active nodes (Simplified)
        if (num_failed_nodes > 0) {
            printf("Master: Redistributing workload due to node failures.\n");

            int active_slaves = size - 1 - num_failed_nodes; //Number of slaves that are alive.

            chunk_index = 0; //Start redistribution at the beginning of full data
            for (int i = 1; i < size; i++)
            {
                if (failed_nodes[i] == 0) //If the slave is alive.
                {
                    // 5.1 Using Non-Blocking Send/Receive + 5.2 Data Compression
                    unsigned char compressed_data[CHUNK_SIZE + 100]; // Add extra space for potential compression expansion
                    uLongf compressed_size = sizeof(compressed_data); // Size of dest buffer
                    compress(compressed_data, &compressed_size, (const Bytef *)&full_data[chunk_index * CHUNK_SIZE], CHUNK_SIZE);

                    MPI_Request request;
                    MPI_Isend(compressed_data, compressed_size, MPI_UNSIGNED_CHAR, i, 0, MPI_COMM_WORLD, &request);
                    MPI_Wait(&request, MPI_STATUS_IGNORE); // Wait for send to complete.

                    chunk_index++;
                }
            }
        }

        printf("Master: Data processing completed.\n");

    } else { // Slave Nodes
        unsigned char compressed_data[CHUNK_SIZE + 100];
        MPI_Status status;

        // 5.1 Using Non-Blocking Send/Receive + 5.2 Data Compression
        MPI_Request recv_request;
        MPI_Irecv(compressed_data, sizeof(compressed_data), MPI_UNSIGNED_CHAR, 0, 0, MPI_COMM_WORLD, &recv_request);
        MPI_Wait(&recv_request, &status); // Wait for receive to complete

        uLongf uncompressed_size = CHUNK_SIZE;
        uncompress((Bytef *)data, &uncompressed_size, compressed_data, status.count);

        printf("Slave %d received data, starting processing...\n", rank);

        process_data(rank, data);

        // 5.1 Using Non-Blocking Send/Receive + 5.2 Data Compression
        unsigned char compressed_data_send[CHUNK_SIZE + 100]; // Add extra space for potential compression expansion
        uLongf compressed_size_send = sizeof(compressed_data_send); // Size of dest buffer
        compress(compressed_data_send, &compressed_size_send, (const Bytef *)data, CHUNK_SIZE);

        MPI_Request send_request;
        MPI_Isend(compressed_data_send, compressed_size_send, MPI_UNSIGNED_CHAR, 0, 0, MPI_COMM_WORLD, &send_request);
        MPI_Wait(&send_request, MPI_STATUS_IGNORE); // Wait for send to complete

        // 6.2 Measure Communication Overhead (on sender)
        int bytes_sent;
        MPI_Pack_size(CHUNK_SIZE, MPI_INT, MPI_COMM_WORLD, &bytes_sent);
        printf("Slave Node %d sent %d bytes to node 0.\n", rank, bytes_sent);

    }

    MPI_Finalize();
    return 0;
}
