sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
export HOME=/root
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8zdb
export LC_ALL=en_US.UTF-8
. /sandbox/env.sh

cd /sandbox/code/github/threefoldtech/jumpscaleX_core
git stash; git fetch -v; git pull origin development; git checkout development -f
cd /sandbox/code/github/threefoldtech/jumpscaleX_threebot
git stash; git fetch -v; git pull origin development; git checkout development -f
js_init generate
. /sandbox/env.sh; kosmos -p 'j.servers.threebot.default.start()'
