from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderSockexec(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.sockexec"

    @builder_method()
    def deps(self):
        """
        kosmos 'j.builders.apps.sockexec.build()'
        build sockexec
        :return:
        """

        self.tools.dir_ensure(self.DIR_BUILD)
        C = """
        cd {DIR_BUILD}
        rm -rf skalibs/
        git clone https://github.com/skarnet/skalibs
        cd {DIR_BUILD}/skalibs
        ./configure
        make
        make install
        rm -rf skalibs
        """
        self._execute(C)

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.apps.sockexec.build()'
        build sockexec
        :return:
        """
        self.tools.dir_ensure(self.DIR_BUILD)
        self.deps()
        C = """
        cd {DIR_BUILD}
        rm -rf /usr/local/lib/skalibs
        ln -sf /usr/lib/skalibs /usr/local/lib/skalibs
        rm -rf sockexec/
        git clone https://github.com/jprjr/sockexec
        cd {DIR_BUILD}/sockexec
        ./configure
        make
        make install
        """
        self._execute(C)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.apps.sockexec.install()'
        Installs the sockexec binary to the correct location
        """
        self._copy("{DIR_BUILD}/sockexec/sockexec", "{DIR_BIN}")

    @builder_method()
    def clean(self):
        self._remove("{DIR_BUILD}/sockexec")
        self._remove(self.DIR_SANDBOX)

    # def start(self, port=7681):
    #     cmd = "/sandbox/bin/sockexec --port {}".format(port)
    #     j.servers.startupcmd.get(name=self.NAME, cmd_start=cmd).start()
    #
    # def running(self):
    #     if len(j.sal.process.getProcessPid(self.NAME)) > 0:
    #         return True
    #     return False
    #
    # def stop(self):
    #     # killing the daemon
    #     pane = j.servers.tmux.pane_get(self.NAME)
    #     pane.kill()
    #
    # @builder_method()
    # def test(self):
    #     if self.running():
    #         self.stop()
    #
    #     self.start()
    #     cc = j.clients.sockexec.get(addr="localhost", port=7681)
    #     assert cc.process_list() == []
    #
    #     cc.process_start("true", "/bin/true")
    #
    #     cc = j.clients.sockexec.get(addr="localhost", port=7681)
    #     assert len(cc.process_list()) == 1
    #
    #     self.stop()
    #     assert self.running() is False
    #     print("TEST OK")
    #
    # @builder_method()
    # def uninstall(self):
    #     bin_path = self.tools.joinpaths("{DIR_BIN}", "sockexec")
    #     self._remove(bin_path)
    #     self.clean()
