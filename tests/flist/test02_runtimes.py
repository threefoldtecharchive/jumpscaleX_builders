import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Runtimes_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("lua", "lua"),
            ("go", "go"),
            ("php", "php-fpm"),
            ("nim", "nim"),
            ("python3", "python3"),
            ("rust", "rustup"),
            ("nodejs", "nodejs")
        ]
    )
    def test_runtimes_flists(self, flist, binary):
        """ SAN-002
        *Test runtimes builers sandbox*
        """
        self.info("Run {} sandbox".format(flist))
        getattr(j.builders.runtimes, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
