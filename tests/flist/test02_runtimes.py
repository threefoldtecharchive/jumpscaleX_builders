import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Runtimes_TestCases(BaseTest):
    @parameterized.expand([("lua", "lua"), ("golang", "golang")])
    def test_runtimes_flists(self, flist, binary):
        """ SAN-002
        *Test runtimes builers sandbox*
        """
        skipped_flists = {
            "lua": "https://github.com/threefoldtech/jumpscaleX/issues/665",
            "golang": "https://github.com/threefoldtech/jumpscaleX/issues/678",
        }

        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("Run {} sandbox".format(flist))
        getattr(j.builders.runtimes, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
