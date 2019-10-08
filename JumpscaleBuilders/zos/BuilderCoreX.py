from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderCoreX(j.baseclasses.builder):
    __jslocation__ = "j.builders.zos.corex"

    def _init(self, **kwargs):
        self.git_url = "https://github.com/threefoldtech/corex.git"
        self.dep_url = "https://github.com/warmcat/libwebsockets"
        self.DIR_BUILD = self._replace("{DIR_TEMP}/corex")
        self.DEP_BUILD = self._replace("{DIR_TEMP}/libwebsocket")

    def dependencies(self):
        """
        install dependencies
        """
        self.tools.dir_ensure(self.DIR_BUILD)
        C = """
        #there are primitives for this TODO:*1
        apt-get update
        apt-get install -y cmake g++ pkg-config git libjson-c-dev libssl-dev vim-runtime libz-dev libcap-dev

        cd {DIR_BUILD}
        rm -rf libwebsockets
        git clone -b v2.4.2 %s
        cd {DIR_BUILD}/libwebsockets
        mkdir build
        cd build
        cmake .. -DLWS_UNIX_SOCK=ON -DLWS_WITHOUT_TESTAPPS=ON -DLWS_WITH_STATIC=OFF
        make -j 4 && make install
        """
        self._execute(C % self.dep_url)

    @builder_method()
    def build(self):
        """
        build corex
        :return:
        """
        self.dependencies()

        self.tools.dir_ensure(self.DIR_BUILD)
        C = """
        cd {DIR_BUILD}
        rm -rf corex/
        git clone %s --branch staging
        cd {DIR_BUILD}/corex
        mkdir build
        cd build
        cmake ..
        make
        ldconfig
        """
        self._execute(C % self.git_url)

    @builder_method()
    def install(self):
        """
        Installs the corex binary to the correct location
        kosmos 'j.builders.apps.corex.install()'
        """
        bin_path = j.builders.tools.joinpaths(self.DIR_BUILD, "corex/build/corex")
        self._copy(bin_path, "{DIR_BIN}")

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """
        dest_path = self.DIR_SANDBOX
        j.builders.web.openresty.sandbox(reset=reset)

        bins = ["corex"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    @builder_method()
    def clean(self):
        self._remove("{DIR_BUILD}/corex")
        self._remove(self.DIR_SANDBOX)

    def start(self, port=7681):
        cmd = "/sandbox/bin/corex --port {}".format(port)
        j.servers.startupcmd.get(name=self._classname, cmd_start=cmd).start()

    def running(self):
        if len(j.sal.process.getProcessPid(self._classname)) > 0:
            return True
        return False

    def stop(self):
        # killing the daemon
        pane = j.servers.tmux.pane_get(self._classname)
        pane.kill()

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        cc = j.clients.corex.get(addr="localhost", port=7681)
        assert cc.process_list() == []

        cc.process_start("true", "/bin/true")

        cc = j.clients.corex.get(addr="localhost", port=7681)
        assert len(cc.process_list()) == 1

        self.stop()
        assert self.running() is False
        print("TEST OK")

    @builder_method()
    def uninstall(self):
        bin_path = self.tools.joinpaths("{DIR_BIN}", "corex")
        self._remove(bin_path)
        self.clean()
