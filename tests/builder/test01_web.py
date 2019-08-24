from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class WebTestCases(BaseTest):
    @parameterized.expand([("caddy", "caddy"), ("traefik", "traefik"), ("nginx", "nginx"), ("openresty", "resty")])
    def test_web_builders(self, builder, process):
        """ BLD-001
        *Test web builers sandbox*
        """
        skipped_builders = {
            "caddy": "https://github.com/threefoldtech/jumpscaleX/issues/654",
            "traefik": "https://github.com/threefoldtech/jumpscaleX/issues/676",
            "openresty": "https://github.com/threefoldtech/jumpscaleX/issues/661",
        }
        if builder in skipped_builders:
            self.skipTest(skipped_builders[builder])

        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.web, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.web, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.web, builder).start()
        except RuntimeError as e:
            self.fail(e)

        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        getattr(j.builders.web, builder).stop()
        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
