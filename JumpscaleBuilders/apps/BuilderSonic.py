from Jumpscale import j
import textwrap

builder_method = j.baseclasses.builder_method


class BuilderSonic(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.sonic"

    @builder_method()
    def _init(self, **kwargs):
        pass

    @builder_method()
    def build(self, reset=False):
        """
        kosmos  'j.builders.apps.sonic.build()'
        :param reset:
        :return:
        """

        j.builders.runtimes.rust.install()

        if not j.core.platformtype.myplatform.platform_is_osx:
            self.system.package.install("clang")
        self.profile.env_set_part("PATH", j.builders.runtimes.rust.DIR_CARGOBIN)
        self._execute("rustup update")
        self._execute("cargo install sonic-server --force", timeout=60 * 60)

    @builder_method()
    def install(self, reset=False):
        """
        kosmos  'j.builders.apps.sonic.install()'
        :param reset:
        :return:
        """
        self._execute("cp %s/sonic /sandbox/bin/" % j.builders.runtimes.rust.DIR_CARGOBIN)

    @builder_method()
    def sandbox(self, zhub_client=None):
        """Copy built bins to dest_path and reate flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type flist_create:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        # ensure dirs
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)

        # sandbox sonic
        bins = ["sonic"]
        for bin in bins:
            self._copy("{DIR_BIN}/" + bin, bin_dest)

        lib_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(bin_dest, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest)
