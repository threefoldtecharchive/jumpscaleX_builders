from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderCockroachDB(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.cockroach"

    def _init(self, **kwargs):
        self.DIR_BUILD = self._replace("{DIR_TEMP}/cockroachdb")

    @builder_method()
    def build(self):
        """
        Builds cockroachdb
        """
        self.tools.dir_ensure(self.DIR_BUILD)
        url = "https://binaries.cockroachdb.com/cockroach-latest.linux-amd64.tgz"
        dest = "{}/cockroach-latest.linux-amd64.tgz".format(self.DIR_BUILD)

        self.tools.file_download(url, to=dest, overwrite=False, expand=True)
        tarpaths = self.tools.find("{DIR_TEMP}", recursive=False, pattern="*cockroach*.tgz", type="f")
        if len(tarpaths) == 0:
            raise j.exceptions.Input(message="could not download:%s, did not find in %s" % (url, self.DIR_BUILD))

        for file in self.tools.find(self.DIR_BUILD, type="f"):
            self._copy(file, "{DIR_BIN}")

    @builder_method()
    def install(self):
        """
        Installs cockroach
        """
        for file in self.tools.find(self.DIR_BUILD, type="f"):
            self._copy(file, "{DIR_BIN}")

    @property
    def startup_cmds(self):
        host = "localhost"
        port = 26257
        http_port = 8581

        cmd = "/sandbox/bin/cockroach start --host={} --insecure --port={} --http-port={}".format(host, port, http_port)
        cmds = [j.servers.startupcmd.get(name=self.NAME, cmd_start=cmd)]
        return cmds

    @builder_method()
    def clean(self):
        self._remove(self.DIR_BUILD)
        self._remove(self.DIR_SANDBOX)

    @builder_method()
    def sandbox(self):
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(bin_dest)
        bin_path = self.tools.joinpaths("{DIR_BIN}", self.NAME)
        self._copy(bin_path, bin_dest)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        pid = j.sal.process.getProcessPid(self.NAME)
        assert pid is not []
        self.stop()

        print("TEST OK")

    @builder_method()
    def uninstall(self):
        bin_path = self.tools.joinpaths("{DIR_BIN}", self.NAME)
        self._remove(bin_path)
        self.clean()
