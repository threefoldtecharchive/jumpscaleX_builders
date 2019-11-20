from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderZdb(j.baseclasses.builder):

    __jslocation__ = "j.builders.db.zdb"

    def _init(self, **kwargs):
        self.git_url = "https://github.com/threefoldtech/0-db.git"
        self.DIR_BUILD = self._replace("{DIR_TEMP}/zdb")

    @builder_method()
    def build(self):
        """
        build zdb
        :return:
        """
        self._dir_ensure(self.DIR_BUILD)
        C = """
        cd {DIR_BUILD}
        rm -rf 0-db/
        git clone https://github.com/threefoldtech/0-db.git --branch development
        cd {DIR_BUILD}/0-db
        make
        """
        self._execute(C)

    @builder_method()
    def install(self):
        """
        Installs the zdb binary to the correct location
        kosmos 'j.builders.db.zdb.install()'
        """
        zdb_bin_path = j.builders.tools.joinpaths(self.DIR_BUILD, "0-db/bin/zdb")
        self._copy(zdb_bin_path, "{DIR_BIN}")

    @property
    def startup_cmds(self):
        addr = "127.0.0.1"
        port = 9900
        datadir = self.DIR_BUILD
        mode = "seq"
        adminsecret = "123456"
        idir = "{}/index/".format(datadir)
        ddir = "{}/data/".format(datadir)
        self._dir_ensure(idir)
        self._dir_ensure(ddir)
        cmd = j.core.tools.text_replace(
            "{DIR_BASE}/bin/zdb --listen {} --port {} --index {} --data {} --mode {} --admin {} --protect"
        ).format(addr, port, idir, ddir, mode, adminsecret)
        cmds = [j.servers.startupcmd.get(name=self._name, cmd_start=cmd)]
        return cmds

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """
        kosmos 'j.builders.db.zdb.sandbox()'

        Copy built bins to dest_path and create flist if create_flist = True

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

        bins = ["zdb"]
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

    @builder_method()
    def clean(self):
        self._remove("{DIR_BUILD}/0-db")
        self._remove(self.DIR_SANDBOX)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        admin_client = j.clients.zdb.client_admin_get()
        namespaces = admin_client.namespaces_list()
        assert namespaces == ["default"]

        admin_client.namespace_new(name="test", maxsize=10)
        namespaces = admin_client.namespaces_list()
        assert namespaces == ["default", "test"]

        admin_client.namespace_delete("test")
        self.stop()

        print("TEST OK")

    @builder_method()
    def uninstall(self):
        bin_path = self._joinpaths("{DIR_BIN}", "zdb")
        self._remove(bin_path)
        self.clean()

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()
