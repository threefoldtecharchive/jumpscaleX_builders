import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Blockchain_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("bitcoind", "bitcoind"),
            ("electrum", "electrum"),
            ("rippled", "ripple"),
            ("atomicswap", "atomicswap"),
            ("geth", "geth"),
            ("tfchain", "tfchaind")
        ]
    )
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

    @parameterized.expand([
        "bitcoind", "electrum", "rippled", "atomicswap", "geth", "tfchain"
    ])
    def tearDownClass(self, cont_name):
        self.info(" * Tear_down!")
        self.info("deleting container {}".format(cont_name))
        container = self.node.containers.get(cont_name)
        self.node.client.container.terminate(container.id)
