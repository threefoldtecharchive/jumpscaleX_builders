import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Apps_TestCases(BaseTest):
    @parameterized.expand([("digitalme", "openresty"), ("freeflow", "apache2"), ("hub", "zerohub"), ("odoo", "odoo")])
    def test_apps_flists(self, flist, binary):
        """ SAN-006
        *Test apps builers sandbox*
        """
        skipped_flists = {
            "hub": "https://github.com/threefoldtech/jumpscaleX/issues/669",
            "odoo": "https://github.com/threefoldtech/jumpscaleX/issues/676",
            "digitalme": "https://github.com/threefoldtech/jumpscaleX/issues/675",
        }
        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.apps, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
