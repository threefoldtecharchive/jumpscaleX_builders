import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Db_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("etcd", "etcd"),
            ("zdb", "zdb"),
            ("postgres", "postgres"),
            ("redis", "redis"),
            ("influxdb", "influx"),
            ("mongodb", "mongod"),
            ("ardb", "ardb"),
            ("mariadb", "mysql"),
        ]
    )
    def test_db_flists(self, flist, binary):
        """ SAN-003
        *Test DB builers sandbox*
        """
        skipped_flists = {
            "etcd": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "zdb": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "postgresql": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "redis": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "mongodb": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "ardb": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "mariadb": "https://github.com/threefoldtech/jumpscaleX/issues/658",
            "influxdb": "https://github.com/threefoldtech/jumpscaleX/issues/690",
        }
        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.db, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))
