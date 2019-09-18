import time
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
    def test_blockchain_builders(self, builder, process):
        """ BLD
        *Test blockchain builers*
        """

        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.blockchain, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.blockchain, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.blockchain, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" Check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.blockchain, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * Check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
