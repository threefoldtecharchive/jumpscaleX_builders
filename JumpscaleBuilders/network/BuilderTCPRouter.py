from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method

CFG = """
[server]
addr = "0.0.0.0"
port = 443
httpport = 80 

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
        j.builders.runtimes.go.install()

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
        self._copy("{DIR_BUILD}/bin/tcprouter", "{DIR_BIN}")
        self._write("{DIR_BASE}/cfg/router.toml", contents=CFG)

    @builder_method()
    def sandbox(self):
        j.builders.db.redis.sandbox()
        self._copy(j.builders.db.redis.DIR_SANDBOX, self.DIR_SANDBOX)
        self._copy("{DIR_BUILD}/bin/tcprouter", "{DIR_SANDBOX}/sandbox/bin/tcprouter")

        self._copy("{DIR_BASE}/cfg/router.toml", "{DIR_SANDBOX}/sandbox/cfg/router.toml")

    @property
    def startup_cmds(self):
        tcprouter_cmd = "tcprouter /sandbox/cfg/router.toml"
        tcprouter = j.servers.startupcmd.get(
            "tcprouter", cmd_start=tcprouter_cmd, path=j.core.tools.text_replace("{DIR_BASE}/bin")
        )
        return [tcprouter]
