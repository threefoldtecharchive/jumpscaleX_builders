from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderInfluxdb(BuilderGolangTools):
    __jslocation__ = "j.builders.db.influxd"

    def profile_builder_set(self):
        super().profile_builder_set()
        self.profile.env_set("GO111MODULE", "on")

    @builder_method()
    def build(self):
        # install dependancies
        self.system.package.mdupdate()
        self.system.package.install(["npm", "bzr"])
        # golang dependancy
        j.builders.runtimes.go.install()

        # build from source
        cmd = """
        cd {DIR_BUILD}
        mkdir -p github && cd github
        rm -rf influxdb
        git clone --depth 1 https://github.com/influxdata/influxdb
        cd influxdb
        go get ./...
        go install ./...
        """
        self._execute(cmd, timeout=2000)

    @builder_method()
    def install(self):
        self.tools.dir_ensure("{DIR_BIN}")
        self._copy(j.core.tools.text_replace("{DIR_BASE}/go_proj/bin/influx", "{DIR_BIN}"))
        self._copy(j.core.tools.text_replace("{DIR_BASE}/go_proj/bin/influxd", "{DIR_BIN}"))

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and reate flist if create_flist = True

        :param reset: reset sandbox file transfer
        :type reset: bool
        :type flist_create:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        bins = ["influx", "influxd"]
        for bin in bins:
            self._copy("{DIR_BIN}/" + bin, bin_dest)

        lib_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(bin_dest, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest)

    def clean(self):
        code_dir = j.sal.fs.joinPaths(self.DIR_BUILD, "github")
        self._remove(code_dir)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @property
    def startup_cmds(self):
        cmds = j.servers.startupcmd.get(name=self._name, cmd_start=self._name)
        return [cmds]

    @builder_method()
    def stop(self):
        j.sal.process.killProcessByName(self._name)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()
        self.start()
        assert self.running()
        print("TEST OK")

