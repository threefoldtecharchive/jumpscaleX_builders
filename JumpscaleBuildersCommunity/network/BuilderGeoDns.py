from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderGeoDns(BuilderGolangTools):
    __jslocation__ = "j.builders.network.geodns"

    def reset(self):
        self._init()

    @builder_method()
    def deps(self):
        j.builders.system.package.mdupdate()
        j.builders.system.package.ensure(["libgeoip-dev", "build-essential", "pkg-config"])
        j.builders.runtimes.go.install(force=False)

    @builder_method()
    def install(self, reset=False):
        """
        installs and builds geodns from github.com/abh/geodns
        """
        if reset is False and self.isInstalled():
            return

        self.deps()
        self.get("github.com/abh/geodns")

        # moving files and creating config
        j.core.tools.dir_ensure("{DIR_BIN}")
        j.builders.tools.file_copy("{DIR_BASE}/go_proj/bin/geodns", "{DIR_BIN}")
        j.builders.tools.dir_ensure("{DIR_VAR}/templates/cfg/geodns/dns", recursive=True)
        j.builders.tools.copyTree("{DIR_VAR}/templates/cfg/geodns", "{DIR_BASE}/cfg/geodns", recursive=True)

    def start(
        self,
        ip="0.0.0.0",
        port="5053",
        config_dir="{DIR_BASE}/cfg/geodns/dns/",
        identifier="geodns_main",
        cpus="1",
        tmux=False,
    ):
        """
        starts geodns server with given params
        """
        if j.builders.tools.dir_exists(config_dir):
            j.core.tools.dir_ensure(config_dir)

        cmd = "{DIR_BIN}/geodns -interface %s -port %s -config=%s -identifier=%s -cpus=%s" % (
            ip,
            str(port),
            config_dir,
            identifier,
            str(cpus),
        )
        cmd = j.builders.tools.replace(cmd)
        s = j.servers.startupcmd.get(self._name)
        s.cmd_start = cmd
        s.executor = "tmux" if tmux else "background"
        s.interpreter = "bash"
        s.timeout = 10
        s.start(reset=True)

    def stop(self):
        """
        stop geodns server with @name
        """
        s = j.servers.startupcmd.get(self._name)
        s.stop()
