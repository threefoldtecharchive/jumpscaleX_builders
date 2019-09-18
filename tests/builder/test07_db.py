from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class DBTestCases(BaseTest):
    @parameterized.expand(
        [
            ("zdb", "zdb"),
            ("etcd", "etcd"),
            ("redis", "redis-server"),
            ("ardb", "ardb"),
            ("postgres", "postgres"),
            ("influxdb", "influx"),
            ("mongodb", "mongod"),
            ("mariadb", "mysql"),
            ("cockroach", "cockroach"),
            ("ledis", "leveldb"),
            ("psql", "psql"),
            ("rocksdb", "rocksdb")
        ]
    )
    def test_db_builders(self, builder, process):
        """ BLD-001
        *Test db builers sandbox*
        """
        skipped_builders = {
            "ledis": "not done yet",
            "mongodb": "not done yet",
            "rocksdb": "where is it"
        }
        if builder in skipped_builders:
            self.skipTest(skipped_builders[builder])
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.db, builder).build(reset=True)
        self.info(" * {}  builder: run install  method.".format(builder))
        getattr(j.builders.db, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.db, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.db, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))
