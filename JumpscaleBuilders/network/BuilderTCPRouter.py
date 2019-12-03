from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


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
        self.get("gopkg.in/redis.v5")
        self.get("github.com/xmonader/tcprouter")
        build_cmd = """
        cd {DIR_TCPROUTER}
        make all
        """
        self._execute(build_cmd)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.network.tcprouter.install()'
        install tcprouter
        """
        self._copy("{DIR_TCPROUTER}/bin/trs", "{DIR_BIN}")
        self._copy("{DIR_TCPROUTER}/bin/trc", "{DIR_BIN}")
        self._copy("{DIR_TCPROUTER}/router.toml", "{DIR_BASE}/cfg/router.toml")

    @builder_method()
    def sandbox(self):
        self._copy("{DIR_TCPROUTER}/bin/trs", "{DIR_SANDBOX}/sandbox/bin/trs")
        self._copy("{DIR_TCPROUTER}/bin/trc", "{DIR_SANDBOX}/sandbox/bin/trc")
        self._copy("{DIR_TCPROUTER}/router.toml", "{DIR_SANDBOX}/sandbox/cfg/router.toml")

    @property
    def startup_cmds(self):
        trs_cmd = self._replace("trs -config {DIR_BASE}/cfg/router.toml")
        # config path trs -config router.toml
        tcprouter_trs = j.servers.startupcmd.get(
            "tcprouter_trs", cmd_start=trs_cmd, path=j.core.tools.text_replace("{DIR_BASE}/bin")
        )
        return [tcprouter_trs]
