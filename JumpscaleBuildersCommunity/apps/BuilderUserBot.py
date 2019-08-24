from Jumpscale import j
import textwrap
from .BuilderDigitalME import BuilderDigitalME

builder_method = j.builders.system.builder_method


class BuilderUserBot(j.builders.system._BaseClass):
    """
    specs:

        - build all required components (only work on ub 1804) using self.build
        - sandbox to sandbox dir
        - create flist
        - in self.test_zos() start the created flist & do the network tests for the openresty

    """

    NAME = "userbot"

    @builder_method()
    def _init(self, **kwargs):
        pass

    @builder_method()
    def build(self, reset=False):
        """
        kosmos 'j.tools.sandboxer.sandbox_build()'

        will build python & openresty & copy all to the right git sandboxes works for Ubuntu only
        :return:
        """
        j.builders.db.zdb.build(reset=reset)

    @builder_method()
    def install(self):
        """
        Installs the zdb binary to the correct location
        """
        j.builders.db.zdb.install()

    @builder_method()

    #     def sandbox(self, reset=False, zhub_client=None, flist_create=True, merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist "):
    #         j.builders.apps.digitalme.sandbox(reset=True)
    #         j.tools.sandboxer.copyTo(j.builders.apps.digitalme.DIR_SANDBOX, self.DIR_SANDBOX)
    #
    #         j.builders.db.zdb.sandbox(reset=True)
    #         j.tools.sandboxer.copyTo(j.builders.db.zdb.DIR_SANDBOX,  self.DIR_SANDBOX)
    #

    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        j.builders.db.zdb.sandbox(reset=reset)
        j.tools.sandboxer.copyTo(j.builders.db.zdb.DIR_SANDBOX, self.DIR_SANDBOX)

        file = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates", "bot_configure.toml")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, "bot_configure.toml")
        self._copy(file, file_dest)

        startup_file = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates", "bot_startup.toml")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, ".startup.toml")
        self._copy(startup_file, file_dest)

        startup_file = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates", "userbot_startup.sh")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, "bot_startup.sh")
        self._copy(startup_file, file_dest)
