from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderBitcoin(j.baseclasses.builder):
    __jslocation__ = "j.builders.blockchain.bitcoind"

    def _init(self, **kwargs):
        self.DIR_BUILD = self._replace("{DIR_VAR}/build/bitcoin")
        j.sal.fs.createDir(self.DIR_BUILD)

    @builder_method()
    def build(self):

        j.builders.buildenv.install()
        self.profile_builder_select()

        # dependancies
        if self.tools.platform_is_ubuntu:
            j.builders.system.package.ensure("g++")
            self.system.package.mdupdate()
            self.system.package.install(
                [
                    "build-essential",
                    "libtool",
                    "autotools-dev",
                    "pkg-config",
                    "libboost-all-dev",
                    "libqt5gui5",
                    "libqt5core5a",
                    "libqt5dbus5",
                    "qttools5-dev",
                    "qttools5-dev-tools",
                    "libprotobuf-dev",
                    "protobuf-compiler",
                    "libqrencode-dev",
                    "autoconf",
                    "openssl",
                    "libssl-dev",
                    "libevent-dev",
                    "libminiupnpc-dev",
                    "bsdmainutils",
                ]
            )

        """
        ' splitting build into 3 steps:
        ' - clone bitcoin source code -v 0.18
        ' - build & link berkly db libs with source code to activate wallet
        ' - executing installation scripts
        """
        # j.clients.git.pullGitRepo(url="https://github.com/bitcoin/bitcoin.git", branch=self.branch)
        clone_bitcoin_script = """
                    cd {DIR_BUILD}
                    git clone https://github.com/bitcoin/bitcoin.git --branch 0.18
                    """
        self._execute(clone_bitcoin_script)

        # berkely db v4.8
        berkly_config = """
            cd {DIR_BUILD}
            wget 'http://download.oracle.com/berkeley-db/db-4.8.30.NC.tar.gz'
            tar -xzvf db-4.8.30.NC.tar.gz
            cd {DIR_BUILD}/db-4.8.30.NC/build_unix/
            ../dist/configure --enable-cxx --disable-shared --with-pic --prefix={DIR_BUILD}/bitcoin
            make install
            """
        self._execute(berkly_config)

        # tag v0.18
        script = """
        cd {DIR_BUILD}/bitcoin
        ./autogen.sh
        ./configure LDFLAGS="-L{DIR_BUILD}/bitcoin/lib/" CPPFLAGS="-I{DIR_BUILD}/bitcoin/include/"
        make
        make install
        """
        self._execute(script, timeout=1000)

    @builder_method()
    def install(self):
        # bitcoin bins
        self._copy("{DIR_BUILD}/bitcoin/src/bitcoind", "{DIR_BIN}")
        self._copy("{DIR_BUILD}/bitcoin/src/bitcoin-cli", "{DIR_BIN}")
        self._copy("{DIR_BUILD}/bitcoin/src/bitcoin-wallet", "{DIR_BIN}")
        self._copy("{DIR_BUILD}/bitcoin/src/bitcoin-tx", "{DIR_BIN}")

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
        bins = (["bitcoind", "bitcoin-cli", "bitcoin-wallet", "bitcoin-tx"],)
        for bin_name in bins:
            dir_src = self._joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self._joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self._dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)
        lib_dest = self._joinpaths(dest_path, "sandbox/lib")
        self._dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self._joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    @property
    def startup_cmds(self):
        # bitcoin daemon
        cmd = j.servers.startupcmd.get(self._name, cmd_start="bitcoind")
        return [cmd]

    @builder_method()
    def stop(self):
        # killing the daemon
        j.sal.process.killProcessByName(self._name)

    @builder_method()
    def clean(self):
        self._remove(self.DIR_BUILD)
        self._remove(self.DIR_SANDBOX)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    """
    testing running daemon
    add tests to bitcoin
    """

    @builder_method()
    def test(self):

        if self.running():
            self.stop()

        self.start()
        assert self.running()

        self._log_info("TEST SUCCESS: Bitcoin daemon is running")
