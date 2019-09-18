from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class LibsTestCases(BaseTest):
    @parameterized.expand(
        [
            ("capnp", "capnp")
        ]
    )
    def test001_libs_builders(self, builder, process):
        """ BLD
        *Test libs builers*
        """
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.libs, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.libs, builder).install()
        self.info(" * {}  builder: run start method.".format(builder))
        try:
            getattr(j.builders.libs, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {}  builder: run stop method.".format(builder))
        try:
            getattr(j.builders.libs, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))

    @parameterized.expand(
        [
            ("libffi", "libtoolize"),
            ("brotli", "brotli"),
            ("openssl", "openssl"),
            ("cmake", "cmake")
        ]
    )
    def test002_libs_builders(self, builder, binary):
        """ BLD
        *Test libs builers*
        """
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.libs, builder).build(reset=True)
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.libs, builder).install()
        self.info(" * check that {} installed successfully.".format(builder))
        self.assertTrue(j.sal.process.execute("which %s") % binary)

