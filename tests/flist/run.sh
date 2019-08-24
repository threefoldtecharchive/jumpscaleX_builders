#!/usr/bin/env bash
JS_BRANCH = "$1"
IYO_USERNAME = "$2"
IYO_CLIENT_ID = "$3"
IYO_CLIENT_SECRET = "$4"
ZOS_NODE_IP = "$5"

cd /sandbox/code/github/threefoldtech/jumpscaleX/
if [ $# -eq 0 ]
  then
  echo "checkout development branch"
    git checkout development
  else
    echo "checkout ${JS_BRANCH} branch"
    git checkout ${JS_BRANCH}
fi
git pull --all
js_init generate
nosetests-3.4 -vs --logging-level=WARNING Jumpscale/builder/test/test_cases.py --tc-file=Jumpscale/builder/test/config.ini --tc=itsyou.username:$IYO_USERNAME --tc=itsyou.client_id:$IYO_CLIENT_ID --tc=itsyou.client_secret=IYO_CLIENT_SECRET --tc=zos_node.node_ip:ZOS_NODE_IP
