import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Db_TestCases(BaseTest):
    @parameterized.expand(
        [
            ("zdb", "zdb"),
            ("etcd", "etcd"),
            ("redis", "redis-server"),
            ("ardb", "ardb"),
            ("influxdb", "influx"),
            ("mongod", "mongod"),
            ("mariadb", "mysql"),
            ("cockroach", "cockroach"),
            ("ledis", "leveldb"),
            ("psql", "psql"),
            ("rocksdb", "rocksdb"),
        ]
    )
    def test_db_flists(self, flist, binary):
        """ SAN-003
        *Test DB builers sandbox*
        """
        skipped_flists = {"ledis": "https://github.com/threefoldtech/jumpscaleX_builders/issues/26"}
        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.db, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        self.assertIn("Usage: ", self.check_container_flist("/sandbox/bin/{} -h".format(binary)))

    @parameterized.expand([
        "zdb", "etcd", "redis", "ardb", "postgres", "influxdb", "mongodb", "cockroach", "ledis", "psql", "rocksdb"
    ])
    def tearDownClass(self, cont_name):
        self.info(" * Tear_down!")
        self.info("deleting container {}".format(cont_name))
        container = self.node.containers.get(cont_name)
        self.node.client.container.terminate(container.id)
