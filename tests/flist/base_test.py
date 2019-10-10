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

    @classmethod
    def setUpClass(cls):
        cls.client_id = config["itsyou"]["client_id"]
        cls.client_secret = config["itsyou"]["client_secret"]
        cls.username = config["itsyou"]["username"]
        cls.node_ip = config["zos_node"]["node_ip"]
        iyo_instance = "iyo_instance_{}".format(randint(1, 1000))
        iyo_client = j.clients.itsyouonline.get(iyo_instance, application_id=cls.client_id, secret=cls.client_secret)
        jwt = iyo_client.jwt_get().jwt
        hub_instance = "hub_instance_{}".format(randint(1, 1000))
        zhub = j.clients.zhub.get(name=hub_instance, token_=jwt, username=cls.username)
        zhub.authenticate()
        zhub.save()

        node_instance = "node_instance_{}".format(randint(1, 1000))
        admin_jwt = iyo_client.jwt_get(name="admin", scope="user:memberof:threefold.sysadmin").jwt
        cls.node = j.clients.zos.get(name=node_instance, password=admin_jwt, host=cls.node_ip)
        cls.sandbox_args = dict(
            zhub_client=zhub,
            reset=True,
            flist_create=True,
            merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX_core-development.flist",
        )

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

    def setUp(self):
        self.container_id = None

    def tearDown(self):
        if self.container_id:
            self.info(" * Tear_down!")
            self.info("deleting container {}".format(self.container_name))
            self.node.client.container.terminate(self.container_id)

    def check_container_flist(self, command):
        data = self.cont_client.system(command).get()
        return data.stdout
