import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Web_TestCases(BaseTest):
    @parameterized.expand([("caddy", "caddy"), ("traefik", "traefik"), ("nginx", "nginx"), ("openresty", "openresty")])
    def test_web_flists(self, flist, binary):
        """ SAN-001
        *Test web builers sandbox*
        """
        skipped_flists = {
            "caddy": "https://github.com/threefoldtech/jumpscaleX/issues/654",
            "traefik": "https://github.com/threefoldtech/jumpscaleX/issues/656",
            "openresty": "https://github.com/threefoldtech/jumpscaleX/issues/661",
        }

        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.web, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
