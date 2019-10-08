import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Apps_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("bootstrapbot", "zdb"),
            ("digitalme", "openresty"),
            ("freeflowpages", "apache2"),
            ("gitea", "gitea"),
            ("graphql", "psql"),
            ("micro", "micro"),
            ("zerohub", "hub"),
            ("odoo", "odoo"),
            ("sockexec", "sockexec"),
            ("userbot", "zdb"),
            ("sonic", "sonic"),
            ("threebot", "lua"),
            ("wordpress", "caddy"),
        ]
    )
    def test_apps_flists(self, flist, binary):
        """ SAN-006
        *Test apps builers sandbox*
        """
        skipped_flists = {
            "wordpress": "https://github.com/threefoldtech/jumpscaleX_builders/issues/13",
            "micro": "https://github.com/threefoldtech/jumpscaleX_builders/issues/24",
        }
        if flist in skipped_flists:
            self.info("run {} sandbox.".format(flist))
        getattr(j.builders.apps, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))

    @parameterized.expand([
        "bootstrapbot",
        "digitalme",
        "freeflow",
        "gitea",
        "graphql",
        "micro",
        "zerohub",
        "odoo",
        "sockexec",
        "userbot",
        "sonic",
        "threebot",
        "wordpress"
    ])
    def tearDown(self, cont_name):
        self.info(" * Tear_down!")
        self.info("deleting container {}".format(cont_name))
        container = self.node.containers.get(cont_name)
        self.node.client.container.terminate(container.id)
