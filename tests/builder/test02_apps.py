from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class AppsTestCases(BaseTest):
    @parameterized.expand(
        [
            ("bootstrapbot", "zdb"),
            ("digitalme", "openresty"),
            ("freeflow", "apache2"),
            ("gitea", "gitea"),
            ("graphql", "psql"),
            ("micro", "micro"),
            ("zerohub", "hub"),
            ("odoo", "odoo"),
            ("sockexec", "sockexec"),
            ("userbot", "zdb"),
            ("sonic", "sonic"),
            ("threebot", "lua"),
            ("wordpress", "caddy")
        ]
    )
    def test_apps_builders(self, builder, process):
        """ BLD-001
        *Test web builers *
        """
        skipped_builders = {
            "wordpress": "not done yet",
            "micro": "not done yet"
        }
        if builder in skipped_builders:
            self.skipTest(skipped_builders[builder])

        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.apps, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.apps, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.apps, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.apps, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
