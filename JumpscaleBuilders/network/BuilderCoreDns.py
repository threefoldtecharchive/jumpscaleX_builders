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
        self.templates_dir = self._joinpaths(j.sal.fs.getDirName(__file__), "templates")

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.network.coredns.build(reset=True)'

        installs and runs coredns server with redis plugin
        """

        # install golang
        j.builders.runtimes.go.install()
        self._dir_ensure(self.package_path)
        # redis as backend
        j.builders.db.redis.install()
        # https://github.com/coredns/coredns#compilation-from-source

        # go to package path and build (for coredns)
        # redis:github.com/andrewayoub/redis is used instead of arvancloud/redis to use the fork which containes fixes for dependencies
        C = """
        cd {}
        git clone https://github.com/coredns/coredns.git
        cd coredns
        echo 'redis:github.com/threefoldtech/coredns-redis' >> plugin.cfg
        export GO111MODULE=on
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
        src = self._joinpaths(self.package_path, name, name)
        self._copy(src, "{DIR_BIN}/coredns")
        self._write("{DIR_BASE}/cfg/coredns.conf", CONFIGTEMPLATE)
        self._execute("service systemd-resolved stop", die=False)

    def clean(self):
        self._remove(self.package_path)
        self._remove(self.DIR_SANDBOX)

    @property
    def startup_cmds(self):
        cmd = j.core.tools.text_replace("{DIR_BASE}/bin/coredns -conf {DIR_BASE}/cfg/coredns.conf")
        cmds = [j.servers.startupcmd.get(name="coredns", cmd_start=cmd)]
        return cmds

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=False):
        j.builders.db.redis.sandbox()

        # add redis binaries
        self._copy(j.builders.db.redis.DIR_SANDBOX, self.DIR_SANDBOX)

        # copy bins
        coredns_bin = self._joinpaths("{DIR_BIN}", self._name)
        bin_dir_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "bin")
        self._dir_ensure(bin_dir_dest)
        self._copy(coredns_bin, bin_dir_dest)

        # config
        config_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "cfg")
        self._copy("{DIR_BASE}/cfg/coredns.conf", config_dest)

        # startup toml
        startup_file = self._joinpaths(self.templates_dir, "coredns_startup.toml")
        self._copy(startup_file, config_dest)

        # add certs
        dir_dest = self._joinpaths(self.DIR_SANDBOX, "etc/ssl/certs/")
        self._dir_ensure(dir_dest)
        self._copy("{DIR_BASE}/cfg/ssl/certs", dir_dest)

    @builder_method()
    def test(self):
        """

        :return:
        """
        raise j.exceptions.NotImplemented
        # TODO

    @builder_method()
    def uninstall(self):
        bin_path = self._joinpaths("{DIR_BIN}", self._name)
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
        assert client.filesystem.list(j.core.tools.text_replace("{DIR_BASE}/bin")[0]["name"] == "coredns")
        client.system(j.core.tools.text_replace("{DIR_BASE}/bin/coredns -dns.port 1053"))
        assert test_container.is_port_listening(1053)
        for job in client.job.list():
            client.job.kill(job["cmd"]["id"])
        print("TEST OK")
