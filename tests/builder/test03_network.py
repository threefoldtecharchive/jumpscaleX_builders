from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Network_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("coredns", "coredns"),
            ("zerotier", "zerotier-one"),
            ("gateone", "gateone"),
            ("geodns", "geodns"),
            ("tcprouter", "tcprouter"),
        ]
    )
    def test_network_builders(self, builder, process):
        """ BLD-001
        *Test network builers*
        """
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.network, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.network, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.network, builder).start()
        except RuntimeError as e:
            self.fail(e)

        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.network, builder).stop()
        except RuntimeError as e:
            self.fail(e)

        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
