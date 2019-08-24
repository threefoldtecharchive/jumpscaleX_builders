from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class VirtualizationTestCases(BaseTest):
    @parameterized.expand([("docker", "containerd")])
    def test_virtualization_builders(self, builder, process):
        """ BLD-001
        *Test virtualization builers sandbox*
        """
        skipped_builders = {"docker": "https://github.com/threefoldtech/jumpscaleX/issues/664"}
        if builder in skipped_builders:
            self.skipTest(skipped_builders[builder])
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.virtualization, builder).build()
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.virtualization, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.virtualization, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.virtualization, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
