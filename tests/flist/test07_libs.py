import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class libs_TestCases(BaseTest):
    @parameterized.expand(
        [("cmake", "cmake"), ("capnp", "capnp"), ("libffi", "libtoolize"), ("Brotli", "brotli"), ("openssl", "openssl")]
    )
    def test_libs_flists(self, flist, binary):
        """ SAN-007
        *Test libs builers sandbox*
        """
        self.info("Run {} sandbox".format(flist))
        getattr(j.builders.libs, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist(j.core.tools.text_replace("{DIR_BASE}/bin/{} -h").format(binary)))

