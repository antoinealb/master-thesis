#!/bin/sh

set -eu

cd $(dirname $0)

mkdir -p ../thesis/figures/plots/

../scripts/plot/plot_lancet.py \
    --data single_node_10_us_synthetic.txt --legend "No replication" \
    --data replicated_2_replicas_10_us_synthetic.txt --legend "2 replicas" \
    --data replicated_2_replicas_10_us_synthetic_leader_only.txt --legend "2 replicas, workload on leader" \
    --ymax 600 \
    --output ../thesis/figures/plots/latency_10us_synthetic.pdf

../scripts/plot/plot_lancet.py \
    --data replicated_2_replicas_0_us_synthetic.txt --legend "2 replicas" \
    --data single_node_0_us_synthetic.txt --legend "No replication" \
    --ymax 80 \
    --output ../thesis/figures/plots/latency_0us_synthetic.pdf

../scripts/plot/plot_lancet.py \
    --data single_node_1_us_synthetic.txt --legend "Unreplicated" \
    --data replicated_3_replicas_1_us_synthetic.txt --legend "3 replicas" \
    --data replicated_5_replicas_1_us_synthetic.txt --legend "5 replicas" \
    --ymax 80 \
    --output ../thesis/figures/plots/cluster_size.pdf
