import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Network_TestCases(BaseTest):
    @parameterized.expand([("coredns", "coredns"), ("zerotier", "zerotier-one")])
    def test_network_flists(self, flist, binary):
        """ SAN-004
        *Test network builers sandbox*
        """
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.network, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
