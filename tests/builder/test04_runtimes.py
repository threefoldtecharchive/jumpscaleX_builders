import time
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Runtimes_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("lua", "lua"),
            ("php", "php-fpm")
        ]
    )
    def test_runtimes_builders(self, builder, process):
        """ BLD-001
        *Test runtimes builers*
        """
        self.info("%s builder: run build method." % builder)
        getattr(j.builders.runtimes, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.runtimes, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.runtimes, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * Check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.runtimes, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * Check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))

    @parameterized.expand(
        [
            ("nim", "nim"),
            ("python3", "python3"),
            ("rust", "rustup"),
            ("nodejs", "nodejs")
        ]
    )
    def test002_runtime_builders(self, builder, binary):
        """ BLD
        *Test runtime builers*
        """
        self.info("%s builder: run build method." % builder)
        getattr(j.builders.runtimes, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.runtimes, builder).install()
        self.info("check that %s installed successfully." % builder)
        self.assertTrue(j.sal.process.execute("which %s") % binary)

    def test003_go(self):
        """ BLD-007
        *Test go builer*
        """
        self.info("go builder: run build method.")
        j.builders.runtimes.go.build(reset=True)
        self.info("go builder: run install method.")
        j.builders.runtimes.go.install()
        self.info("Check that go builder installed successfully")
        self.assertTrue(j.builders.runtimes.go.is_installed)
