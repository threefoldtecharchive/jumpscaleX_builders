import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Blockchain_TestCases(BaseTest):
    @parameterized.expand([("ripple", "ripple")])
    def test_blockchain_flists(self, flist, binary):
        """ SAN-009
        *Test blockchain builers sandbox*
        """
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.blockchain, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} help".format(binary)))
