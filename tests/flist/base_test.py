import time
import requests
from loguru import logger
from random import randint
from testconfig import config
from unittest import TestCase
from Jumpscale import j


class BaseTest(TestCase):
    LOGGER = logger
    LOGGER.add("flist_{time}.log")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = config["itsyou"]["client_id"]
        self.client_secret = config["itsyou"]["client_secret"]
        self.username = config["itsyou"]["username"]
        self.node_ip = config["zos_node"]["node_ip"]

    def setUp(self):
        self.iyo_instance = "iyo_instance_{}".format(randint(1, 1000))
        self.iyo_client = j.clients.itsyouonline.get(
            self.iyo_instance, application_id=self.client_id, secret=self.client_secret
        )
        self.jwt = self.iyo_client.jwt_get().jwt
        self.hub_instance = "hub_instance_{}".format(randint(1, 1000))
        self.zhub = j.clients.zhub.get(name=self.hub_instance, token_=self.jwt, username=self.username)
        self.zhub.authenticate()
        self.zhub.save()

        self.node_instance = "node_instance_{}".format(randint(1, 1000))
        self.admin_jwt = self.iyo_client.jwt_get(name="admin", scope="user:memberof:threefold.sysadmin").jwt
        self.node = j.clients.zos.get(name=self.node_instance, password=self.admin_jwt, host=self.node_ip)
        self.sandbox_args = dict(
            zhub_client=self.zhub,
            reset=True,
            flist_create=True,
            merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX_core-development.flist",
        )
        self.info("* Test case : {}".format(self._testMethodName))

    def info(self, message):
        self.LOGGER.info(message)

    def deploy_flist_container(self, builder):
        self.cont = self.node.client.container.create(
            "https://hub.grid.tf/{}/{}_merged_tf-autobuilder_threefoldtech-jumpscaleX_core-development.flist".format(
                self.username, builder
            )
        )
        self.container_id = self.cont.get()
        self.container_name = "{}_container".format(builder)
        self.cont_client = self.node.client.container.client(self.container_id)

    def tearDown(self):
        self.info(" * Tear_down!")
        self.info("deleting container {}".format(self.container_name))
        self.node.client.container.terminate(self.container_id)

    def check_container_flist(self, command):
        data = self.cont_client.system(command).get()
        return data.stdout
