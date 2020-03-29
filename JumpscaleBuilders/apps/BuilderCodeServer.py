from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderCodeServer(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.codeserver"

    def _init(self):
        self.RELEASE_VERSION = "2.1698"
        self.TAR_VERSION = "2.1698-vsc1.41.1"

    @builder_method()
    def build(self):
        """
        kosoms 'j.builders.apps.codeserver.build()'
        """
        # TODO: check what deps were used for here... seems to work ok on fresh container
        # deps = """
        # gcc libx11-dev libxkbfile-dev libsecret-1-dev pkg-config
        # """
        # j.builders.system.package.ensure(deps)
        self._execute(
            "cd {DIR_TEMP}; wget -c https://github.com/cdr/code-server/releases/download/%s/code-server%s-linux"
            "-x86_64.tar.gz" % (self.RELEASE_VERSION, self.TAR_VERSION)
        )
        self._execute("cd {DIR_TEMP}; tar -xvzf code-server%s-linux-x86_64.tar.gz" % self.TAR_VERSION)

    @builder_method()
    def install(self, reset=False):
        """
        kosmos  'j.builders.apps.codeserver.install()'
        :param reset:
        :return:
        """
        if not reset and j.sal.fs.exists("{DIR_BIN}/code-server"):
            return
        if reset:
            self._remove("{DIR_BIN}/code-server")
        self._copy("{DIR_TEMP}/code-server%s-linux-x86_64/code-server" % self.TAR_VERSION, "{DIR_BIN}")

    def clean(self):
        self._remove("{DIR_TEMP}/code-server%s-linux-x86_64/code-server" % self.TAR_VERSION)
        self._remove("{DIR_TEMP}/code-server%s-linux-x86_64" % self.TAR_VERSION)
        self._remove("{DIR_TEMP}/code-server%s-linux-x86_64.tar.gz" % self.TAR_VERSION)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()
        self._remove("{DIR_BIN}/code-server")

    @property
    def startup_cmds(self):
        cmd = "code-server --auth none"
        cmds = [j.servers.startupcmd.get(name=self._name, cmd_start=cmd)]
        return cmds

    @builder_method()
    def uninstall(self):
        if self.running():
            self.stop()
        self._remove("{DIR_BIN}/code-server")

    @builder_method()
    def sandbox(self):
        """
        kosmos 'j.builders.apps.codeserver.sandbox()'
        """
        bin_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "bin")
        self._dir_ensure(bin_dest)

        bins = ["code-server"]
        for bin in bins:
            self._copy("{DIR_BIN}/" + bin, bin_dest)

        # startup toml file
        templates_dir = self._joinpaths(j.sal.fs.getDirName(__file__), "templates")
        startup_file = self._joinpaths(templates_dir, "codeserver_startup.toml")
        self._copy(startup_file, f"{self.DIR_SANDBOX}/.startup.toml")

        lib_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "lib")
        self._dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self._joinpaths(bin_dest, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest)
