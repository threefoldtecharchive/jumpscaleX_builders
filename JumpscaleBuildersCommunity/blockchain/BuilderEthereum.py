from Jumpscale import j
from Jumpscale.builders.runtimes.BuilderGolang import BuilderGolangTools

builder_method = j.builders.system.builder_method


class BuilderEthereum(BuilderGolangTools):
    NAME = "geth"

    def _init(self, **kwargs):
        super()._init()
        self.geth_repo = "github.com/ethereum/go-ethereum"
        self.package_path = self.package_path_get("ethereum/go-ethereum")

    @builder_method()
    def build(self, reset=False):
        """Build the binaries of ethereum
        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """
        j.builders.runtimes.golang.install()

        self.get(self.geth_repo)

        self._execute("cd {} && go build -a -ldflags '-w -extldflags -static' ./cmd/geth".format(self.package_path))
        self._execute("cd {} && go build -a -ldflags '-w -extldflags -static' ./cmd/bootnode".format(self.package_path))

    @builder_method()
    def install(self, reset=False):
        """
        Install the binaries of ethereum
        """
        bin_path = self.tools.joinpaths(self.package_path, self.NAME)
        self.tools.dir_ensure("{DIR_BIN}")
        self.tools.file_copy(bin_path, self._replace("{DIR_BIN}"))

    @property
    def startup_cmds(self):
        cmd = j.servers.startupcmd.get("geth", cmd_start="geth")
        return [cmd]

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
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
        dest_path = self.DIR_SANDBOX
        self.profile_sandbox_select()
        dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, "geth")
        dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
        self.tools.dir_ensure(dir_dest)
        self._copy(dir_src, dir_dest)
        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    def test(self):
        """Tests the builder by performing the following:
        build(), install(), start()-> geth running, stop()-> geth not running
        """
        if self.running():
            self.stop()
        self.build(reset=True)
        self.install()

        assert not self.running()
        # check start is working
        self.start()
        assert self.running()
        # check stop is working
        self.stop()
        assert not self.running()
        self._log_info("Ethereum test successfull")
