from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolang import BuilderGolangTools

builder_method = j.builders.system.builder_method

CFG = """
[server]
addr = "0.0.0.0"
port = 443

[server.dbbackend]
type 	 = "redis"
addr     = "127.0.0.1"
port     = 6379
refresh  = 10
"""


class BuilderTCPRouter(BuilderGolangTools):
    __jslocation__ = "j.builders.network.tcprouter"

    @builder_method()
    def _init(self, **kwargs):
        super()._init()
        self.DIR_TCPROUTER = self.package_path_get("xmonader/tcprouter")

    @builder_method()
    def configure(self):
        pass

    @builder_method()
    def build(self):
        j.builders.runtimes.golang.install()

        self.get("github.com/xmonader/tcprouter")
        build_cmd = """
        cd {DIR_TCPROUTER}
        go build -ldflags \"-linkmode external -s -w -extldflags -static\" -o {DIR_BUILD}/bin/tcprouter
        """
        self._execute(build_cmd)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.network.tcprouter.install()'
        install tcprouter
        """
        j.builders.db.redis.install()
        self.tools.file_copy(self._replace("{DIR_BUILD}/bin/tcprouter"), "{DIR_BIN}")
        j.sal.fs.writeFile(filename="/sandbox/cfg/router.toml", contents=CFG)

    @builder_method()
    def sandbox(self):
        j.builders.db.redis.sandbox()
        self.tools.copyTree(j.builders.db.redis.DIR_SANDBOX, self.DIR_SANDBOX)
        self.tools.file_copy(
            self._replace("{DIR_BUILD}/bin/tcprouter"), self._replace("{DIR_SANDBOX}/sandbox/bin/tcprouter")
        )

        self.tools.file_copy(
            self._replace("/sandbox/cfg/router.toml"), self._replace("{DIR_SANDBOX}/sandbox/cfg/router.toml")
        )

    @property
    def startup_cmds(self):
        tcprouter_cmd = "tcprouter /sandbox/cfg/router.toml"
        tcprouter = j.servers.startupcmd.get("tcprouter", cmd_start=tcprouter_cmd, path="/sandbox/bin")
        return [tcprouter]
