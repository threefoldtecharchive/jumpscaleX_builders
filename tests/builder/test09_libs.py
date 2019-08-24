from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class LibsTestCases(BaseTest):
    @parameterized.expand([("capnp", "capnp"), ("syncthing", "syncthing")])
    def test_libs_builders(self, builder, process):
        """ BLD-001
        *Test libs builers sandbox*
        """
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.libs, builder).build()
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

    def test002_libffi(self):
        """ BLD-028
        *Test libffi builer sandbox*
        """
        self.info(" * libffi builder: run build method.")
        j.builders.libs.libffi.build(reset=True)
        self.info(" * libffi builder: run install method.")
        j.builders.libs.libffi.install()
        try:
            self.info(" * check that libffi is installed successfully")
            j.sal.process.execute("which libtoolize")
        except:
            self.assertTrue(False)

    def test003_brotli(self):
        """ BLD-029
        *Test brotli builer sandbox*
        """
        self.info(" * brotli builder: run build method.")
        j.builders.libs.brotli.build(reset=True)
        self.info(" * brotli builder: run install method.")
        j.builders.libs.brotli.install()
        try:
            self.info(" * check that brotli is installed successfully")
            j.sal.process.execute("which brotli")
        except:
            self.assertTrue(False)

    def test004_openssl(self):
        """ BLD-032
        *Test openssl builer sandbox*
        """
        self.info(" * openssl builder: run build method.")
        j.builders.libs.openssl.build(reset=True)
        self.info(" * openssl builder: run install method.")
        j.builders.libs.openssl.install()
        try:
            self.info(" * check that openssl is installed successfully")
            j.sal.process.execute("which openssl")
        except:
            self.assertTrue(False)
