import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Virtualization_TestCases(BaseTest):
    @parameterized.expand([("docker", "dockerd-ce")])
    def test_network_flists(self, flist, binary):
        """ SAN-005
        *Test Virtualization builers sandbox*
        """
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.virtualization, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))

    @parameterized.expand(["docker"])
    def tearDownClass(self, cont_name):
        self.info(" * Tear_down!")
        self.info("deleting container {}".format(cont_name))
        container = self.node.containers.get(cont_name)
        self.node.client.container.terminate(container.id)
