#!/usr/bin/env python3
"""
Lab 5 Simulation: Scaling Multi-node Programs

This single-machine simulation demonstrates:
1. Master bottleneck when all data-path operations go through the master.
2. P2P hash-based replication among slave nodes.
3. Master only does initial partitioning and final result gathering.
4. User-level checkpointing and recovery after a process/node failure.

Run examples:
    python lab5_sim.py --mode both --nodes 6 --partitions 24
    python lab5_sim.py --mode p2p --nodes 8 --partitions 40 --fail-node 3
    python lab5_sim.py --mode master --nodes 10 --partitions 100

No external libraries are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


CHECKPOINT_DIR = Path("checkpoints_lab5")


def stable_hash(text: str) -> int:
    """Deterministic hash. Do not use Python's built-in hash() because it is salted."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def sleep_for_network(delay: float) -> None:
    """Artificial network/processing delay so bottlenecks become visible."""
    if delay > 0:
        time.sleep(delay)


@dataclass
class Partition:
    partition_id: int
    values: List[int]

    def compute(self) -> int:
        """A simple task: sum this partition."""
        return sum(self.values)


@dataclass
class Node:
    node_id: int
    ip: str
    network_delay: float

    # Primary partitions owned by this node.
    primary: Dict[int, Partition] = field(default_factory=dict)

    # Replica partitions received from peers.
    replicas: Dict[int, Partition] = field(default_factory=dict)

    # Computed result for primary partitions.
    results: Dict[int, int] = field(default_factory=dict)

    alive: bool = True

    @property
    def name(self) -> str:
        return f"Node {self.node_id}"

    def receive_primary(self, partition: Partition) -> None:
        self._require_alive()
        sleep_for_network(self.network_delay)
        self.primary[partition.partition_id] = partition

    def receive_replica(self, partition: Partition) -> None:
        self._require_alive()
        sleep_for_network(self.network_delay)
        self.replicas[partition.partition_id] = partition

    def process_primary_partitions(self) -> None:
        self._require_alive()
        for pid, partition in self.primary.items():
            sleep_for_network(self.network_delay)
            self.results[pid] = partition.compute()

    def checkpoint(self, directory: Path = CHECKPOINT_DIR) -> Path:
        """
        User-level checkpointing: save application state to disk.
        This is enough for teaching. In real systems, one can use checkpointing libraries.
        """
        directory.mkdir(exist_ok=True)
        path = directory / f"node_{self.node_id}.json"
        state = {
            "node_id": self.node_id,
            "ip": self.ip,
            "primary": {
                str(pid): part.values for pid, part in self.primary.items()
            },
            "replicas": {
                str(pid): part.values for pid, part in self.replicas.items()
            },
            "results": {str(pid): value for pid, value in self.results.items()},
        }
        path.write_text(json.dumps(state, indent=2))
        return path

    def fail(self) -> None:
        """Simulate process/node failure: memory is lost."""
        self.alive = False
        self.primary.clear()
        self.replicas.clear()
        self.results.clear()

    def restart_from_checkpoint(self, directory: Path = CHECKPOINT_DIR) -> bool:
        """Restart node process and restore saved state."""
        path = directory / f"node_{self.node_id}.json"
        self.alive = True
        if not path.exists():
            return False

        state = json.loads(path.read_text())
        self.primary = {
            int(pid): Partition(int(pid), values)
            for pid, values in state.get("primary", {}).items()
        }
        self.replicas = {
            int(pid): Partition(int(pid), values)
            for pid, values in state.get("replicas", {}).items()
        }
        self.results = {
            int(pid): result
            for pid, result in state.get("results", {}).items()
        }
        return True

    def has_partition(self, partition_id: int) -> bool:
        return partition_id in self.primary or partition_id in self.replicas

    def read_partition(self, partition_id: int) -> Partition | None:
        self._require_alive()
        if partition_id in self.primary:
            return self.primary[partition_id]
        return self.replicas.get(partition_id)

    def _require_alive(self) -> None:
        if not self.alive:
            raise RuntimeError(f"{self.name} is down")


class Master:
    """
    Master node.

    In master-centric mode:
        Master also handles replication and keeps metadata.

    In P2P mode:
        Master only partitions input and gathers final results.
        Master does NOT store replica metadata.
    """

    def __init__(self, network_delay: float) -> None:
        self.network_delay = network_delay
        self.master_messages = 0
        self.replica_metadata: Dict[int, List[int]] = {}

    def send_to_node(self, node: Node, partition: Partition, as_replica: bool = False) -> None:
        sleep_for_network(self.network_delay)
        self.master_messages += 1
        if as_replica:
            node.receive_replica(partition)
        else:
            node.receive_primary(partition)

    def gather_results(self, nodes: List[Node]) -> Dict[int, int]:
        all_results: Dict[int, int] = {}
        for node in nodes:
            sleep_for_network(self.network_delay)
            self.master_messages += 1
            all_results.update(node.results)
        return all_results


class Lab5Simulation:
    def __init__(
        self,
        num_nodes: int,
        num_partitions: int,
        replication_factor: int,
        values_per_partition: int,
        master_delay: float,
        p2p_delay: float,
        seed: int,
    ) -> None:
        random.seed(seed)
        self.num_nodes = num_nodes
        self.num_partitions = num_partitions
        self.replication_factor = replication_factor
        self.values_per_partition = values_per_partition
        self.master_delay = master_delay
        self.p2p_delay = p2p_delay
        self.seed = seed

        self.nodes = [
            Node(node_id=i + 1, ip=f"10.0.0.{i + 1}", network_delay=p2p_delay)
            for i in range(num_nodes)
        ]
        self.master = Master(network_delay=master_delay)
        self.partitions = self._make_partitions()

        self.p2p_replication_messages = 0

    def _make_partitions(self) -> List[Partition]:
        partitions = []
        for pid in range(self.num_partitions):
            values = [random.randint(1, 100) for _ in range(self.values_per_partition)]
            partitions.append(Partition(pid, values))
        return partitions

    def owner_for_partition(self, partition_id: int) -> Node:
        """Initial partitioning by master. Simple round-robin."""
        return self.nodes[partition_id % self.num_nodes]

    def replica_nodes_for_partition(self, partition_id: int, owner: Node) -> List[Node]:
        """
        Hash-based replica placement.

        For each candidate slave node, compute:
            H(slave_ip, partition_id)

        The lowest hash values are selected as replica locations.
        This can be recomputed during reads. Master need not store metadata.
        """
        candidates = [node for node in self.nodes if node.node_id != owner.node_id]
        ranked = sorted(
            candidates,
            key=lambda node: stable_hash(f"{node.ip}:{partition_id}")
        )
        return ranked[: self.replication_factor]

    def reset_checkpoints(self) -> None:
        if CHECKPOINT_DIR.exists():
            shutil.rmtree(CHECKPOINT_DIR)
        CHECKPOINT_DIR.mkdir(exist_ok=True)

    def run_master_centric(self, fail_node: int | None = None) -> Dict[str, float | int | str]:
        """
        Baseline/problem design:
        Master is on the data path for primary placement, replication, and result collection.
        """
        self.reset_checkpoints()
        start = time.perf_counter()

        # 1. Master partitions input and sends primary partitions.
        for partition in self.partitions:
            owner = self.owner_for_partition(partition.partition_id)
            self.master.send_to_node(owner, partition, as_replica=False)

        # 2. Master handles replication and stores metadata.
        for partition in self.partitions:
            owner = self.owner_for_partition(partition.partition_id)
            replicas = self.replica_nodes_for_partition(partition.partition_id, owner)
            self.master.replica_metadata[partition.partition_id] = [n.node_id for n in replicas]
            for replica_node in replicas:
                self.master.send_to_node(replica_node, partition, as_replica=True)

        # 3. Each node checkpoints local state.
        for node in self.nodes:
            node.checkpoint()

        # 4. Simulate failure and restore checkpoint.
        recovery_status = "no failure simulated"
        if fail_node is not None:
            victim = self.nodes[fail_node - 1]
            victim.fail()
            ok = victim.restart_from_checkpoint()
            recovery_status = (
                f"{victim.name} recovered from local checkpoint"
                if ok else f"{victim.name} had no checkpoint"
            )

        # 5. Process and gather results through master.
        for node in self.nodes:
            node.process_primary_partitions()
            node.checkpoint()

        results = self.master.gather_results(self.nodes)

        elapsed = time.perf_counter() - start
        return {
            "mode": "MASTER-CENTRIC",
            "nodes": self.num_nodes,
            "partitions": self.num_partitions,
            "master_messages": self.master.master_messages,
            "p2p_replication_messages": self.p2p_replication_messages,
            "result_partitions": len(results),
            "final_sum": sum(results.values()),
            "elapsed_seconds": round(elapsed, 4),
            "recovery_status": recovery_status,
        }

    def run_p2p(self, fail_node: int | None = None) -> Dict[str, float | int | str]:
        """
        Improved design:
        Master only does primary placement and final result gathering.
        Slave nodes replicate partitions directly to peers using hash-based mapping.
        """
        self.reset_checkpoints()
        start = time.perf_counter()

        # 1. Master sends each primary partition to its owner only.
        for partition in self.partitions:
            owner = self.owner_for_partition(partition.partition_id)
            self.master.send_to_node(owner, partition, as_replica=False)

        # 2. Slave nodes do P2P replication. Master is not involved.
        for partition in self.partitions:
            owner = self.owner_for_partition(partition.partition_id)
            replica_nodes = self.replica_nodes_for_partition(partition.partition_id, owner)

            for replica_node in replica_nodes:
                sleep_for_network(self.p2p_delay)
                self.p2p_replication_messages += 1
                replica_node.receive_replica(partition)

        # 3. Each node checkpoints local state.
        for node in self.nodes:
            node.checkpoint()

        # 4. Demonstrate replica lookup without master metadata.
        sample_reads = self.demo_hash_based_reads(limit=5)

        # 5. Simulate failure and restore checkpoint.
        recovery_status = "no failure simulated"
        if fail_node is not None:
            victim = self.nodes[fail_node - 1]
            victim.fail()
            ok = victim.restart_from_checkpoint()
            recovery_status = (
                f"{victim.name} recovered from local checkpoint"
                if ok else f"{victim.name} had no checkpoint"
            )

        # 6. Process and gather results through master.
        for node in self.nodes:
            node.process_primary_partitions()
            node.checkpoint()

        results = self.master.gather_results(self.nodes)

        elapsed = time.perf_counter() - start
        return {
            "mode": "P2P-HASH-REPLICATION",
            "nodes": self.num_nodes,
            "partitions": self.num_partitions,
            "master_messages": self.master.master_messages,
            "p2p_replication_messages": self.p2p_replication_messages,
            "result_partitions": len(results),
            "final_sum": sum(results.values()),
            "elapsed_seconds": round(elapsed, 4),
            "recovery_status": recovery_status,
            "sample_reads": sample_reads,
        }

    def demo_hash_based_reads(self, limit: int = 5) -> str:
        """
        During reads, any client/node can recompute the same hash function to locate replicas.
        Master has no replica metadata in P2P mode.
        """
        samples = []
        for partition in self.partitions[:limit]:
            owner = self.owner_for_partition(partition.partition_id)
            replicas = self.replica_nodes_for_partition(partition.partition_id, owner)
            locations = [owner.node_id] + [node.node_id for node in replicas]
            samples.append(f"P{partition.partition_id}->N{locations}")
        return ", ".join(samples)


def print_report(report: Dict[str, float | int | str]) -> None:
    print("\n" + "=" * 72)
    print(f"MODE: {report['mode']}")
    print("=" * 72)
    print(f"Nodes                         : {report['nodes']}")
    print(f"Data partitions               : {report['partitions']}")
    print(f"Master messages               : {report['master_messages']}")
    print(f"P2P replication messages      : {report['p2p_replication_messages']}")
    print(f"Result partitions gathered    : {report['result_partitions']}")
    print(f"Final computed sum            : {report['final_sum']}")
    print(f"Elapsed time                  : {report['elapsed_seconds']} sec")
    print(f"Recovery status               : {report['recovery_status']}")
    if "sample_reads" in report:
        print(f"Hash-based read examples      : {report['sample_reads']}")
    print(f"Checkpoint files              : {CHECKPOINT_DIR.resolve()}")


def build_sim(args: argparse.Namespace) -> Lab5Simulation:
    return Lab5Simulation(
        num_nodes=args.nodes,
        num_partitions=args.partitions,
        replication_factor=args.replicas,
        values_per_partition=args.values,
        master_delay=args.master_delay,
        p2p_delay=args.p2p_delay,
        seed=args.seed,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lab 5 simulation: master bottleneck vs P2P replication and checkpoint recovery."
    )
    parser.add_argument("--mode", choices=["master", "p2p", "both"], default="both")
    parser.add_argument("--nodes", type=int, default=6, help="Number of slave/worker nodes")
    parser.add_argument("--partitions", type=int, default=24, help="Number of data partitions")
    parser.add_argument("--replicas", type=int, default=2, help="Replica copies per partition")
    parser.add_argument("--values", type=int, default=500, help="Integers per partition")
    parser.add_argument("--fail-node", type=int, default=3, help="Node number to fail and recover")
    parser.add_argument("--no-failure", action="store_true", help="Disable failure simulation")
    parser.add_argument("--master-delay", type=float, default=0.002, help="Delay per master message")
    parser.add_argument("--p2p-delay", type=float, default=0.0005, help="Delay per P2P/local message")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if args.nodes < 2:
        raise SystemExit("Use at least 2 nodes.")
    if args.replicas >= args.nodes:
        raise SystemExit("--replicas must be less than --nodes.")
    if args.fail_node < 1 or args.fail_node > args.nodes:
        raise SystemExit("--fail-node must be between 1 and --nodes.")

    fail_node = None if args.no_failure else args.fail_node

    if args.mode in ("master", "both"):
        sim = build_sim(args)
        print_report(sim.run_master_centric(fail_node=fail_node))

    if args.mode in ("p2p", "both"):
        sim = build_sim(args)
        print_report(sim.run_p2p(fail_node=fail_node))

    print("\nTeaching point:")
    print("  Master-centric design increases master traffic as nodes/partitions grow.")
    print("  P2P design keeps heavy replication traffic among slaves.")
    print("  Hash(slave IP, partition ID) lets nodes locate replicas without master metadata.")
    print("  Local checkpoints let each node restart after simulated failure.")


if __name__ == "__main__":
    main()
