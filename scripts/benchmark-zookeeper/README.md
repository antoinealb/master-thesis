# ZooKeeper experimental setup

This folder contains the setup code for a small zookeeper (zk) cluster.
The cluster contains 3 virtual machines which is the minimum for having consensus.
All the machines are running Ubuntu 16.04

It is managed using [Vagrant](https://www.vagrantup.com/) to allow for easy VM integration.

## Starting the cluster

```bash
# First boot all the VMs and install zookeeper on them
vagrant up

# Then SSH into each of them and start zookeeper

for i in $(seq 3)
do
    vagrant ssh box$i -- zookeeper-3.4.13/bin/zkServer.sh start
done
```

## Interacting with ZooKeeper

This command will give you a zookeeper shell running on box1.
Feel free to change the machine, it does not matter.

```
vagrant ssh box1 -- zookeeper-3.4.13/bin/zkCli.sh
```

You can now try commands such as `create /foo 12`, `get /foo` or `set /foo 14`.
See `help` for details.

