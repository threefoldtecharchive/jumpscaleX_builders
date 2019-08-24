from Jumpscale import j
from Jumpscale.builders.runtimes.BuilderGolang import BuilderGolangTools

builder_method = j.builders.system.builder_method


class BuilderEtcd(BuilderGolangTools):
    NAME = "etcd"

    def _init(self):
        super()._init()

    def profile_builder_set(self):
        super().profile_builder_set()
        self.profile.env_set("GO111MODULE", "on")

    @builder_method()
    def build(self):
        """
        Build etcd
        """
        j.builders.runtimes.golang.install()
        # https://github.com/etcd-io/etcd/blob/master/Documentation/dl_build.md#build-the-latest-version
        self.get("go.etcd.io/etcd")
        self.get("go.etcd.io/etcd/etcdctl")

    @builder_method()
    def install(self):
        j.builders.tools.file_copy("%s/etcd" % self.DIR_GO_PATH_BIN, "{DIR_BIN}/etcd")
        j.builders.tools.file_copy("%s/etcdctl" % self.DIR_GO_PATH_BIN, "{DIR_BIN}/etcdctl")

    @property
    def startup_cmds(self):
        return [j.servers.startupcmd.get(name=self.NAME, cmd_start=self.NAME)]

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """
        Copy built bins to dest_path and create flist if create_flist = True
        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        etcd_bin_path = self.tools.joinpaths(self._replace("{DIR_BIN}"), self.NAME)
        etcdctl_bin_path = self.tools.joinpaths(self._replace("{DIR_BIN}"), "etcdctl")
        self.tools.file_copy(etcd_bin_path, bin_dest)
        self.tools.file_copy(etcdctl_bin_path, bin_dest)

        lib_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in [self.NAME, "etcdctl"]:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    def client_get(self, name):
        """
        return the client to the installed server, use the config params of the server to create a client for
        :return:
        """
        return j.clients.etcd.get(name)

    def test(self):

        self.stop()
        self.install()
        self.sandbox()

        # try to start/stop
        tmux_pane = j.servers.etcd.start()
        tmux_process = tmux_pane.process_obj
        child_process = tmux_pane.process_obj_child
        assert child_process.is_running()

        client = self.client_get("etcd_test")
        j.sal.nettools.waitConnectionTest(client.host, client.port)
        client.api.put("foo", "etcd_bar")
        assert client.get("foo") == "etcd_bar"
        j.servers.etcd.stop(tmux_process.pid)

        print("TEST OK")
