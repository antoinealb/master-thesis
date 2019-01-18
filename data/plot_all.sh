#!/bin/sh

set -eu

cd $(dirname $0)

mkdir -p ../thesis/figures/plots/

../scripts/plot/plot_lancet.py \
    --data replicated_2_replicas_10_us_synthetic.txt --legend "2 replicas" \
    --data single_node_dpdk_10us_synthetic.txt --legend "No replication" \
    --output ../thesis/figures/plots/latency_10us_synthetic.pdf
