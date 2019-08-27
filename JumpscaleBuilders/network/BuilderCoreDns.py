from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


CONFIGTEMPLATE = """
. {
    redis  {
        address 127.0.0.1:6379
    }
    forward 8.8.8.8 9.9.9.9 

}
"""


class BuilderCoreDns(BuilderGolangTools, j.baseclasses.builder):
    __jslocation__ = "j.builders.network.coredns"

    def _init(self, **kwargs):
        super()._init()
        self.package_path = self.package_path_get(self._name)
        self.templates_dir = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates")

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.network.coredns.build(reset=True)'

        installs and runs coredns server with redis plugin
        """

        # install golang
        j.builders.runtimes.go.install()
        self.tools.dir_ensure(self.package_path)
        # redis as backend
        j.builders.db.redis.sandbox()
        # https://github.com/coredns/coredns#compilation-from-source

        # go to package path and build (for coredns)
        # redis:github.com/andrewayoub/redis is used instead of arvancloud/redis to use the fork which containes fixes for dependencies
        C = """
        cd {}
        git clone https://github.com/coredns/coredns.git
        cd coredns
        echo 'redis:github.com/andrewayoub/redis' >> plugin.cfg
        make
        """.format(
            self.package_path
        )
        self._execute(C, timeout=1000)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.network.coredns.install()'

        installs and runs coredns server with redis plugin
        """
        name = "coredns"
        src = self.tools.joinpaths(self.package_path, name, name)
        self._copy(src, "{DIR_BIN}/coredns")
        j.sal.fs.writeFile(filename="/sandbox/cfg/coredns.conf", contents=CONFIGTEMPLATE)
        self._execute("service systemd-resolved stop", die=False)

    def clean(self):
        self._remove(self.package_path)
        self._remove(self.DIR_SANDBOX)

    @property
    def startup_cmds(self):
        cmd = "/sandbox/bin/coredns -conf /sandbox/cfg/coredns.conf"
        cmds = [j.servers.startupcmd.get(name="coredns", cmd_start=cmd)]
        return cmds

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=False):

        # add redis binaries
        self.tools.copyTree(j.builders.db.redis.DIR_SANDBOX, self.DIR_SANDBOX)

        # copy bins
        coredns_bin = j.sal.fs.joinPaths("{DIR_BIN}", self._name)
        bin_dir_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dir_dest)
        self._copy(coredns_bin, bin_dir_dest)

        # config
        config_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "cfg")
        self._copy("/sandbox/cfg/coredns.conf", config_dest)

        # startup toml
        startup_file = self.tools.joinpaths(self.templates_dir, "coredns_startup.toml")
        self._copy(startup_file, config_dest)

        # add certs
        dir_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "etc/ssl/certs/")
        self.tools.dir_ensure(dir_dest)
        self._copy("/sandbox/cfg/ssl/certs", dir_dest)

    @builder_method()
    def test(self):
        """

        :return:
        """
        raise j.exceptions.NotImplemented
        # TODO

    @builder_method()
    def uninstall(self):
        bin_path = self.tools.joinpaths("{DIR_BIN}", self._name)
        self._remove(bin_path)
        self.clean()

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def test_zos(self, zos_client="", zhub_client=""):
        self.sandbox(zhub_client=zhub_client, flist_create=True)
        flist = "https://hub.grid.tf/{}/coredns.flist".format(zhub_client.username)
        test_container = zos_client.containers.create(
            name="test_coredns", flist=flist, ports={1053: 1053}, host_network=True
        )
        client = test_container.client
        assert client.ping()
        assert client.filesystem.list("/sandbox/bin")[0]["name"] == "coredns"
        client.system("/sandbox/bin/coredns -dns.port 1053")
        assert test_container.is_port_listening(1053)
        for job in client.job.list():
            client.job.kill(job["cmd"]["id"])
        print("TEST OK")
