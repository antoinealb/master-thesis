#!/bin/sh

set -eu

cd $(dirname $0)

mkdir -p ../thesis/figures/plots/

../scripts/plot/plot_lancet.py \
    --data single_node_10_us_synthetic.txt --legend "Unreplicated" -m "x-" \
    --data replicated_3_replicas_10_us_synthetic.txt --legend "3 replicas" -m "o-" \
    --data replicated_3_replicas_10_us_synthetic_singlethread.txt --legend "3 replicas (no worker thread)" -m "o--" \
    --ymax 400 \
    --output ../thesis/figures/plots/latency_10us_synthetic.pdf

../scripts/plot/plot_lancet.py \
    --data single_node_1_us_synthetic.txt --legend "Unreplicated" -m "x-" \
    --data replicated_3_replicas_1_us_synthetic.txt --legend "3 replicas" -m "o-" \
    --data replicated_3_replicas_1_us_synthetic_singlethread.txt --legend "3 replicas (no worker thread)" -m "o--" \
    --ymax 80 \
    --output ../thesis/figures/plots/latency_1us_synthetic.pdf

../scripts/plot/plot_lancet.py \
    --data single_node_1_us_synthetic.txt --legend "Unreplicated" -m "x-" \
    --data replicated_3_replicas_1_us_synthetic.txt --legend "3 replicas" -m "o-" \
    --data replicated_5_replicas_1_us_synthetic.txt --legend "5 replicas" -m "v-" \
    --ymax 80 \
    --output ../thesis/figures/plots/cluster_size_1us.pdf

../scripts/plot/plot_lancet.py \
    --data single_node_10_us_synthetic.txt --legend "Unreplicated" -m "x-" \
    --data replicated_3_replicas_10_us_synthetic.txt --legend "3 replicas" -m "o-" \
    --data replicated_5_replicas_10_us_synthetic.txt --legend "5 replicas" -m "v-" \
    --ymax 400 \
    --output ../thesis/figures/plots/cluster_size_10us.pdf
