import warnings
import re
warnings.filterwarnings("ignore")
from fabric.api import *

env.user = 'kogias'

def hostname(machine_id):
    return "icnals{:02d}.iccluster.epfl.ch".format(machine_id)

def _get_node_id():
    return int(re.search(r'icnals(\d+)', env.host_string).group(1))

def _get_peers():
    current = _get_node_id()
    return [p for p in env.raft_peers if p != current]


LANCET_COORDINATOR = hostname(10)

def all():
    env.hosts = [hostname(c) for c in [8, 7, 10, 12, 13, 14, 15, 18, 20]]

def single(node):
    node = int(node)
    env.hosts = [hostname(node)]


def lancet_coord():
    env.hosts = [LANCET_COORDINATOR]

def raft3():
    env.hosts = [hostname(c) for c in [12, 18]]
    env.raft_peers = [12, 18, 20]

def raft5():
    env.hosts = [hostname(c) for c in [7, 16, 12, 18]]
    env.raft_peers = [7, 16, 12, 18, 20]

def run_raft():
    peer_args = ["-p 10.90.44.2{peer:02d}:8000:{peer}".format(peer=peer) for peer in _get_peers()]
    cmd = 'netstack/netstack/apps/r2p2-server-dpdk -c 0x03 -m 2048 -- -i {} '.format(_get_node_id())
    cmd = cmd + " ".join(peer_args)

    with cd('~/antoinealb/rpchol/build'):
        sudo(cmd)


def run_lancet(leader):
    cmd = "~/antoinealb/lancet/coordinator/coordinator " \
            "--targetHost 10.90.44.2{leader}:8000 " \
            "--loadAgents icnals14 " \
            "-loadBinary agents/t_rpclib_agent --loadThread 8 --loadConn 128 " \
            "--ltAgents icnals10 --ltThreads --ltConn 32 --latBinary agents/l_rpclib_agent --lqps 4000 " \
            "--iadist exp " \
            "--proto synthetic:fixed:10 " \
            "--loadPattern step:30000:10000 " \
            "--duration 70"

    with cd('~/antoinealb/lancet'):
        run(cmd.format(leader=leader))

def generate_deploy_key():
    local('ssh-keygen -t rsa -b 4096 -f github_deploy_key -N ""')
    print("All set, your key is:")
    with open('github_deploy_key.pub') as f:
        print(f.read())

def copy_deploy_key():
    run('rm -f ~/antoinealb/github_deploy_key')
    put('github_deploy_key', '~/antoinealb/github_deploy_key')
    run('chmod 400 ~/antoinealb/github_deploy_key')

def clone():
    with cd('~/antoinealb'):
        with shell_env(GIT_SSH_COMMAND='ssh -i ~/antoinealb/github_deploy_key -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'):
            run('git clone git@github.com:antoinealb/rpchol.git')

        with cd('rpchol'):
            run('git config --local user.email antoine@antoinealb.net')
            run('git config --local user.name Antoine Albertelli')

def checkout(branch):
    with cd('~/antoinealb/rpchol'):
        run('git checkout {}'.format(branch))

def cmake():
    run('rm -rf ~/antoinealb/rpchol/build')
    run('mkdir ~/antoinealb/rpchol/build')
    with cd('~/antoinealb/rpchol/build'):
        run('cmake ../src -DWITH_DPDK=ON -DCMAKE_BUILD_TYPE=Release')

def make():
    with cd('~/antoinealb/rpchol/build'):
        run('make -j16')

def unittest():
    with cd('~/antoinealb/rpchol/build'):
        run('make test')

def uname():
    run('uname -a')

def prepare():
    run('mkdir -p ~/antoinealb')
    copy_deploy_key()
    with cd('~/antoinealb'):
        run('rm -rf rpchol')
