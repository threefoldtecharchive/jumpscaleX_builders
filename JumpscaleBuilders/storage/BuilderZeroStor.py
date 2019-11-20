from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method

CONFIG_TEMPLATE = """
namespace: default  # 0-db namespace (required)
datastor: # required
  # the address(es) of a 0-db cluster (required0)
  shards: # required
    - 127.0.0.1:9900
  pipeline:
    block_size: 4096
    compression: # optional
      type: snappy # snappy is the default
      mode: default # default is the default
metastor: # required
  db: # required
    # the address(es) of an etcd server cluster
    type: "etcd"
    config:
        endpoints:
        - 127.0.0.1:2379
  encoding: protobuf
"""


class BuilderZeroStor(BuilderGolangTools):
    __jslocation__ = "j.builders.storage.zstor"

    def _init(self, **kwargs):
        super()._init()
        self.datadir = ""

    def profile_builder_set(self):
        super().profile_builder_set()

    @builder_method()
    def build(self):
        """
        Builds zstor
        """
        j.builders.runtimes.go.install()
        self.get("github.com/threefoldtech/0-stor/cmd/zstor")

        # make to generate bin
        cmd = "cd {}/src/github.com/threefoldtech/0-stor && make".format(self.DIR_GO_PATH)
        self._execute(cmd)

    @builder_method()
    def install(self):
        """
        Installs zstor
        """
        # dependencies
        j.builders.db.etcd.install()
        j.builders.db.zdb.install()

        self._copy("{}/src/github.com/threefoldtech/0-stor/bin".format(self.DIR_GO_PATH), "{DIR_BIN}")
        self._write("{DIR_BASE}/cfg/zstor.yaml", CONFIG_TEMPLATE)

    @property
    def startup_cmds(self):
        """
        Starts zstor
        """
        self.datadir = self.DIR_BUILD
        self._dir_ensure(self.datadir)

        cmd = "zstor --config {DIR_BASE}/cfg/zstor.yaml daemon --listen 127.0.0.1:8000"
        cmd_zdb = j.builders.db.zdb.startup_cmds
        cmd_etcd = j.builders.db.etcd.startup_cmds
        cmds = [j.servers.startupcmd.get(name=self._classname, cmd_start=cmd)]
        return cmd_zdb + cmd_etcd + cmds

    @builder_method()
    def clean(self):
        """
        Remove built files
        """
        self._remove(self.DIR_SANDBOX)
        self._remove("{}/src/github.com/threefoldtech/0-stor/".format(self.DIR_GO_PATH))

    @builder_method()
    def sandbox(self):
        """
        Copy required bin files to be used to sandbox
        """
        # Copy zstor bins
        bin_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "bin")
        self._dir_ensure(bin_dest)
        bin_path = self._joinpaths(self._replace("{DIR_BIN}"), self._classname)
        bin_bench_path = self._joinpaths(self._replace("{DIR_BIN}"), "zstorbench")
        self._copy(bin_path, bin_dest)
        self._copy(bin_bench_path, bin_dest)

        # Copy zdb bin and lib
        j.builders.db.zdb.sandbox()
        bin_src = self._joinpaths(j.builders.db.zdb.DIR_SANDBOX, "sandbox/bin")
        self._copy(bin_src, bin_dest)

        lib_src = self._joinpaths(j.builders.db.zdb.DIR_SANDBOX, "sandbox/lib")
        lib_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "lib")
        self._dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(lib_src, lib_dest, exclude_sys_libs=False)

        # Copy etcd bin and lib
        j.builders.db.etcd.sandbox()
        bin_src = self._joinpaths(j.builders.db.etcd.DIR_SANDBOX, "sandbox/bin")
        self._copy(bin_src, bin_dest)

        lib_src = self._joinpaths(j.builders.db.etcd.DIR_SANDBOX, "sandbox/lib")
        lib_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "lib")
        self._dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(lib_src, lib_dest, exclude_sys_libs=False)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        pid = j.sal.process.getProcessPid(self._classname)
        assert pid is not []
        self.stop()

        print("TEST OK")

    @builder_method()
    def uninstall(self):
        """
        Uninstall zstor by removing all related files from bin directory and build destination
        """
        bin_path = self._joinpaths("{DIR_BIN}", self._classname)
        bin_bench_path = self._joinpaths("{DIR_BIN}", "zstorbench")
        self._remove(bin_path)
        self._remove(bin_bench_path)
        self.clean()
