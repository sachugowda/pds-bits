# Lab 5: Larger-Scale Multi-Node Programs with P2P Replication and Checkpoint Recovery

## 1. Title

**Explore multi-node programs at larger scale using P2P replication, hash-based replica lookup, and checkpoint-based recovery.**

---

## 2. Lab Objective

The objective of this lab is to understand the scalability problem in a master-slave distributed system and implement an improved design where slave nodes replicate data among themselves without involving the master node.

By the end of this lab, students will be able to:

1. Explain why the master node becomes a bottleneck when the cluster size increases.
2. Differentiate between master-centric replication and peer-to-peer replication.
3. Use hash-based mapping to decide where replica partitions should be stored.
4. Understand how reads can locate replicas without storing replica metadata at the master.
5. Implement simple user-level checkpointing for each node.
6. Simulate node/process failure and recover node state from checkpoints.

---

## 3. Problem Statement

In a basic master-slave distributed system, the master node performs many operations:

- It partitions the input data.
- It sends partitions to worker nodes.
- It handles data replication.
- It collects results from all nodes.
- It may also maintain metadata about where replicas are stored.

This design works for small clusters. However, when more nodes and data partitions are added, the master becomes overloaded.

The main problem is:

> The master node becomes a bottleneck because too much data traffic passes through it.

For large-scale systems, the master should coordinate the system, but it should not be involved in every data movement operation.

---

## 4. Proposed Solution

The solution is to move data replication away from the master.

In this lab, we use a **peer-to-peer replication method**.

### Master responsibilities

The master performs only two main tasks:

1. Initial data partitioning.
2. Final result gathering.

### Slave node responsibilities

Slave nodes perform:

1. Local processing of assigned partitions.
2. Peer-to-peer replication of partitions.
3. Local checkpointing.
4. Recovery from checkpoint after failure.

### Key idea

Instead of asking the master where to store replicas, each node independently computes replica locations using:

```text
hash(slave IP address, partition ID)
```

This means:

- The master does not store replica metadata.
- Any node can recompute the same hash to locate replicas.
- Replication traffic is distributed among slave nodes.
- The master load is reduced.

---

## 5. Concepts Used in This Lab

### 5.1 Data Partition

A data partition is a smaller block of the full input data.

Example:

```text
Partition 0 = [42, 20, 51, 84, ...]
Partition 1 = [18, 45, 12, 91, ...]
```

In the simulation, each partition contains a list of random numbers.

The computation performed is:

```text
result = sum of all numbers in the partition
```

---

### 5.2 Primary Partition

The primary partition is the original partition assigned to a node by the master.

Example:

```text
Partition 2 -> Node 3
```

Here, Node 3 is the primary owner of Partition 2.

---

### 5.3 Replica Partition

A replica is an additional copy of a partition stored on another node.

Example:

```text
Partition 2 -> Node 3   Primary copy
Partition 2 -> Node 5   Replica copy
Partition 2 -> Node 4   Replica copy
```

Replica copies are useful for fault tolerance and data availability.

---

### 5.4 Master-Centric Replication

In master-centric replication, the master sends both primary partitions and replica partitions.

Example:

```text
Master -> Node 3  Primary partition
Master -> Node 5  Replica
Master -> Node 4  Replica
```

This increases the number of messages handled by the master.

---

### 5.5 Peer-to-Peer Replication

In P2P replication, the master sends only the primary partition.

After that, the primary node sends replicas directly to peer nodes.

Example:

```text
Master -> Node 3  Primary partition

Node 3 -> Node 5  Replica
Node 3 -> Node 4  Replica
```

This reduces the master load.

---

### 5.6 Hash-Based Replica Mapping

The program uses a deterministic hash function to select replica nodes.

For every candidate slave node, the program computes:

```text
hash(slave IP address, partition ID)
```

The nodes with the smallest hash values are selected as replica locations.

This makes replica placement deterministic.

If the same input is given again, the same replica locations are found.

---

### 5.7 Checkpointing

A checkpoint is a saved snapshot of a node's current state.

In this lab, each node saves the following information:

```text
node_id
ip address
primary partitions
replica partitions
computed results
```

The checkpoint is saved as a JSON file.

Example:

```text
checkpoints_lab5/node_3.json
```

If a node fails, its memory is cleared. Then it can restart by reading its checkpoint file.

Checkpointing is similar to saving progress in a game:

```text
Save state -> failure happens -> reload saved state
```

---

## 6. Program Used

The simulation program is:

```text
lab5_sim.py
```

This program compares two modes:

| Mode | Meaning |
|---|---|
| `master` | Master-centric replication |
| `p2p` | Peer-to-peer hash-based replication |
| `both` | Runs both modes and compares them |

---

## 7. Step-by-Step Tutorial to Run the Program

### Step 1: Create a folder for the lab

Open the terminal and create a new folder.

```bash
mkdir lab5
cd lab5
```

---

### Step 2: Copy the Python program into the folder

Place the file `lab5_sim.py` inside the `lab5` folder.

Check whether the file is present:

```bash
ls
```

Expected output:

```text
lab5_sim.py
```

---

### Step 3: Run the program in both modes

```bash
python3 lab5_sim.py --mode both --nodes 6 --partitions 24
```

This command runs:

1. Master-centric replication.
2. P2P hash-based replication.

---

## 8. Meaning of Command-Line Arguments

| Argument | Meaning |
|---|---|
| `--mode both` | Run both master-centric and P2P modes |
| `--mode master` | Run only master-centric mode |
| `--mode p2p` | Run only P2P mode |
| `--nodes 6` | Create 6 slave nodes |
| `--partitions 24` | Create 24 data partitions |
| `--replicas 2` | Create 2 replicas per partition |
| `--fail-node 3` | Simulate failure of Node 3 |
| `--no-failure` | Disable failure simulation |

---

## 9. Sample Run

Command:

```bash
python3 lab5_sim.py --mode both --nodes 6 --partitions 24
```

Sample output:

```text
========================================================================
MODE: MASTER-CENTRIC
========================================================================
Nodes                         : 6
Data partitions               : 24
Master messages               : 78
P2P replication messages      : 0
Result partitions gathered    : 24
Final computed sum            : 598378
Elapsed time                  : 0.2785 sec
Recovery status               : Node 3 recovered from local checkpoint

========================================================================
MODE: P2P-HASH-REPLICATION
========================================================================
Nodes                         : 6
Data partitions               : 24
Master messages               : 30
P2P replication messages      : 48
Result partitions gathered    : 24
Final computed sum            : 598378
Elapsed time                  : 0.1929 sec
Recovery status               : Node 3 recovered from local checkpoint
Hash-based read examples      : P0->N[1, 5, 3], P1->N[2, 6, 5]
```

---

## 10. Explanation of the Output

### 10.1 Master-Centric Mode

```text
Master messages = 78
P2P replication messages = 0
```

In master-centric mode, the master handles:

```text
primary partition sending + replica sending + result gathering
```

For 24 partitions, 6 nodes, and 2 replicas per partition:

```text
Primary sends        = 24
Replica sends        = 24 × 2 = 48
Result gathering     = 6
Total master messages = 24 + 48 + 6 = 78
```

So the master handles 78 messages.

This shows the bottleneck.

---

### 10.2 P2P Hash Replication Mode

```text
Master messages = 30
P2P replication messages = 48
```

In P2P mode, the master handles only:

```text
primary partition sending + final result gathering
```

For 24 partitions and 6 nodes:

```text
Primary sends        = 24
Result gathering     = 6
Total master messages = 24 + 6 = 30
```

Replication is now done between slave nodes:

```text
P2P replication messages = 24 × 2 = 48
```

Therefore, the master load is reduced.

---

### 10.3 Comparing Both Modes

| Metric | Master-Centric | P2P Hash Replication |
|---|---:|---:|
| Master messages | 78 | 30 |
| P2P replication messages | 0 | 48 |
| Final result | Same | Same |
| Scalability | Lower | Better |

The final computed sum is the same in both modes. This means both methods are correct.

However, the P2P method reduces master load.

---

## 11. Understanding the Checkpoint Files

After execution, a folder is created:

```text
checkpoints_lab5
```

Check the folder:

```bash
ls checkpoints_lab5
```

Example output:

```text
node_1.json  node_2.json  node_3.json  node_4.json  node_5.json  node_6.json
```

Each file contains the saved state of one node.

To see Node 3's checkpoint:

```bash
cat checkpoints_lab5/node_3.json
```

A checkpoint contains:

```json
{
  "node_id": 3,
  "ip": "10.0.0.3",
  "primary": {
    "2": [...],
    "8": [...],
    "14": [...],
    "20": [...]
  },
  "replicas": {
    "...": [...]
  },
  "results": {
    "2": 23763,
    "8": 25368,
    "14": 25185,
    "20": 25207
  }
}
```

Here:

```text
2, 8, 14, 20 are partition IDs.
23763, 25368, 25185, 25207 are computed sums.
```

So:

```text
Partition 2  -> sum = 23763
Partition 8  -> sum = 25368
Partition 14 -> sum = 25185
Partition 20 -> sum = 25207
```

---

## 12. Why Node 3 Gets Partitions 2, 8, 14, and 20

The program assigns partitions using round-robin allocation.

For 6 nodes:

```text
Partition 0  -> Node 1
Partition 1  -> Node 2
Partition 2  -> Node 3
Partition 3  -> Node 4
Partition 4  -> Node 5
Partition 5  -> Node 6
Partition 6  -> Node 1
Partition 7  -> Node 2
Partition 8  -> Node 3
...
```

Therefore, Node 3 gets:

```text
Partition 2, 8, 14, 20
```

---

## 13. Failure and Recovery Demonstration

By default, the program simulates failure of Node 3.

Command:

```bash
python3 lab5_sim.py --mode p2p --nodes 6 --partitions 24 --fail-node 3
```

The program performs the following steps:

1. Creates data partitions.
2. Assigns partitions to nodes.
3. Creates replicas using P2P replication.
4. Saves checkpoint files.
5. Simulates failure of Node 3.
6. Clears Node 3's memory.
7. Restarts Node 3.
8. Loads Node 3's checkpoint file.
9. Continues computation.

Expected recovery message:

```text
Recovery status : Node 3 recovered from local checkpoint
```

---

## 14. Useful Commands for Experiments

### Run only master-centric mode

```bash
python3 lab5_sim.py --mode master --nodes 6 --partitions 24
```

### Run only P2P mode

```bash
python3 lab5_sim.py --mode p2p --nodes 6 --partitions 24
```

### Run both modes with more nodes

```bash
python3 lab5_sim.py --mode both --nodes 10 --partitions 100
```

### Run without failure simulation

```bash
python3 lab5_sim.py --mode both --nodes 6 --partitions 24 --no-failure
```

### Change the number of replicas

```bash
python3 lab5_sim.py --mode both --nodes 8 --partitions 40 --replicas 3
```

---

## 15. Expected Observation

When the number of partitions increases, master-centric mode shows higher master traffic.

Example:

```bash
python3 lab5_sim.py --mode both --nodes 10 --partitions 100
```

In master-centric mode:

```text
Master messages = primary sends + replica sends + result gathering
```

In P2P mode:

```text
Master messages = primary sends + result gathering
```

Therefore:

```text
P2P replication reduces master load.
```

---

## 16. Algorithm

### 16.1 Master-Centric Algorithm

```text
Input: data partitions, slave nodes, replication factor

1. Master creates data partitions.
2. Master assigns each partition to a primary node.
3. Master sends the primary partition to the selected node.
4. Master selects replica nodes.
5. Master sends replica copies to the selected replica nodes.
6. Each node saves a checkpoint.
7. Simulate node failure.
8. Failed node restarts from checkpoint.
9. Each node computes results for its primary partitions.
10. Master gathers final results.
```

---

### 16.2 P2P Hash Replication Algorithm

```text
Input: data partitions, slave nodes, replication factor

1. Master creates data partitions.
2. Master assigns each partition to a primary node.
3. Master sends the primary partition to the selected node.
4. Primary node computes replica locations using:
       hash(slave IP address, partition ID)
5. Primary node sends replicas directly to peer nodes.
6. Each node saves a local checkpoint.
7. Simulate node failure.
8. Failed node restarts from checkpoint.
9. Each node computes results for its primary partitions.
10. Master gathers final results.
```

---

## 17. Result Interpretation

Students should compare:

```text
Master messages
P2P replication messages
Elapsed time
Final computed sum
Recovery status
```

Important conclusions:

1. P2P design reduces master traffic.
2. Final result remains correct.
3. Hashing allows replica lookup without master metadata.
4. Checkpointing allows recovery from node failure.
5. The master is used for coordination, not for all data movement.

---

## 18. Viva Questions

1. Why does the master become a bottleneck in large-scale distributed systems?
2. What is the difference between master-centric replication and P2P replication?
3. Why do we use a hash function for replica placement?
4. What is stored in a checkpoint file?
5. What is the difference between replication and checkpointing?
6. Why should the master not store replica metadata in this lab?
7. How does the system locate replicas during read?
8. What happens when a node fails?
9. Why is the final computed sum the same in both modes?
10. What happens if the number of replicas is increased?

---

## 19. Student Exercise

Modify the experiment and record observations.

| Experiment | Command | Observation |
|---|---|---|
| Increase nodes | `--nodes 10` | Compare master messages |
| Increase partitions | `--partitions 100` | Compare elapsed time |
| Increase replicas | `--replicas 3` | Check replication traffic |
| Disable failure | `--no-failure` | Observe recovery message |
| Fail another node | `--fail-node 5` | Check checkpoint recovery |

---

## 20. Final Conclusion

This lab demonstrates that a master-centric distributed design does not scale well because the master handles too much data-path traffic.

The P2P hash-based replication design improves scalability by allowing slave nodes to replicate data directly among themselves.

Checkpointing adds fault tolerance by allowing failed nodes to recover their previous state from locally saved checkpoint files.

The main lesson is:

> In scalable distributed systems, the master should coordinate the system, but heavy data transfer should be distributed among worker nodes.
