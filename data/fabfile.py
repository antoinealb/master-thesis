import warnings
warnings.filterwarnings("ignore")
from fabric.api import *

env.user = 'kogias'


def all():
    env.hosts = ['icnals{:02d}.iccluster.epfl.ch'.format(c) for c in [8, 7, 10, 12, 13, 14, 15, 18, 20]]

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

def prepare():
    run('mkdir -p ~/antoinealb')
    copy_deploy_key()
    with cd('~/antoinealb'):
        run('rm -rf rpchol')
