import time
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Runtimes_TestCases(BaseTest):
    @parameterized.expand([("lua", "openresty"), ("php", "php-fpm")])
    def test_runtimes_builders(self, builder, process):
        """ BLD-001
        *Test runtimes builers sandbox*
        """
        self.info("%s builder: run build method." % builder)
        getattr(j.builders.runtimes, builder).build()
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.runtimes, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.runtimes, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * Check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.runtimes, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * Check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))

    def test002_golang(self):
        """ BLD-007
        *Test golang builer sandbox*
        """
        self.info("golang builder: run build method.")
        j.builders.runtimes.golangtools.build(reset=True)
        self.info("golang builder: run install method.")
        j.builders.runtimes.golangtools.install()
        self.info("Check that golang builder installed successfully")
        self.assertTrue(j.builders.runtimes.golangtools.is_installed)

    def test003_nimlang(self):
        """ BLD-009
        *Test nimlang builer sandbox*
        """
        j.builders.runtimes.nimlang.build(reset=True)
        j.builders.runtimes.nimlang.install()
        try:
            j.sal.process.execute("which nim")
        except:
            self.assertTrue(False)

    def test004_python(self):
        """ BLD-010
        *Test python builer sandbox*
        """
        j.builders.runtimes.python.build(reset=True)
        j.builders.runtimes.python.install()
        try:
            j.sal.process.execute("which python")
        except:
            self.assertTrue(False)

    def test005_rust(self):
        """ BLD-011
        *Test rust builer sandbox*
        """
        self.info("rust builder: run build method.")
        j.builders.runtimes.rust.build(reset=True)
        self.info("rust builder: run install method.")
        j.builders.runtimes.rust.install()
        self.info("rust that nodejs installed successfully.")
        try:
            j.sal.process.execute("which rustup")
        except:
            self.assertTrue(False)

    def test006_nodejs(self):
        """ BLD-012
        *Test nodejs builer sandbox*
        """
        self.info("nodejs builder: run build method.")
        j.builders.runtimes.nodejs.build(reset=True)
        self.info("nodejs builder: run install method.")
        j.builders.runtimes.nodejs.install()
        self.info("check that nodejs installed successfully.")
        self.assertTrue(j.sal.process.execute("which nodejs"))
