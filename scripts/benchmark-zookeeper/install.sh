#!/bin/bash

set -eu

ZK_VERSION=3.4.13
SRC=$(dirname $0)

# First install java
sudo apt-get install -y default-jre

cd ~
rm -rf zookeeper-*
wget "http://www-eu.apache.org/dist/zookeeper/zookeeper-$ZK_VERSION/zookeeper-$ZK_VERSION.tar.gz"
tar xf zookeeper-$ZK_VERSION.tar.gz

rm -rf zkdata
mkdir zkdata

cp $SRC/zookeeper.conf zookeeper-$ZK_VERSION/conf/zoo.cfg
$SRC/zk_id_from_ip.py > zkdata/myid

# Then install python3 for benchmarking needs
sudo apt-get install -y python3-pip
sudo pip3 install kazoo
