sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
export HOME=/root
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8zdb
export LC_ALL=en_US.UTF-8
ssh-keygen -t rsa -N "" -f my.key && eval `ssh-agent` && ssh-add
apt-get update -y
rm -rf /sandbox/lib/python3.6/site-packages/zerohub-nspkg.pth
export DEBIAN_FRONTEND="noninteractive"

apt install -y openssh-server locales curl git rsync unzip lsb

cp -r /sandbox_threebot_linux64/* /
echo messagebus:x:51 >> /etc/group
echo crontab:x:50 >> /etc/group
echo root:x:0:0::/root:/bin/bash >> /etc/passwd
useradd _apt
. /sandbox/env.sh
jsx configure  -s

unset PYTHONPATH
unset PYTHONHOME
. /sandbox/env.sh
apt-get install --reinstall python3

apt install apt-utils libgeoip1 libgeoip-dev geoip-bin tmux -y
pip3 install setuptools wheel bottle_websocket graphviz capnp
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
apt-get install clang -y

cd /sandbox/code/github/threefoldtech/jumpscaleX_core
git stash; git fetch -v; git pull origin development; git checkout development -f
cd /sandbox/code/github/threefoldtech/jumpscaleX_threebot
git stash; git fetch -v; git pull origin development; git checkout development -f
cd /sandbox/code/github/threefoldtech/jumpscaleX_libs
git stash; git fetch -v; git pull origin development; git checkout development -f

. /sandbox/env.sh; kosmos -p 'j.server.threebot.local_start_default()'
. /sandbox/env.sh&&jsx wiki-load
