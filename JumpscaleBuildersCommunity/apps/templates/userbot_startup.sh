sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
export HOME=/root
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8zdb
export LC_ALL=en_US.UTF-8
. /sandbox/env.sh

cp /sandbox/code/github/threefoldtech/digitalmeX/packages/init_bot/chatflows/bot_init.py /sandbox/code/github/threefoldtech/digitalmeX/DigitalMe/tools/openpublish/base_chatflows/
cp /sandbox/code/github/threefoldtech/digitalmeX/packages/init_bot/actors/userbot.py /sandbox/code/github/threefoldtech/digitalmeX/DigitalMe/tools/openpublish/base_actors/


kosmos "bcdb = j.data.bcdb.new(name='userbotsettings'); bcdb.models_add('/sandbox/code/github/threefoldtech/digitalmeX/packages/init_bot/models'); model = bcdb.model_get('threebot.user.initialization'); model.new({'name': 'user_initialization', 'token': j.data.idgenerator.generateGUID()}).save()"
tmux new -d -s main  "export NACL_SECRET=123 ; kosmos 'j.servers.threebot.default.servers_start()'"
