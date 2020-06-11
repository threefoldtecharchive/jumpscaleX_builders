from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderGrafanaAdmin(j.baseclasses.builder):

    __jslocation__ = "j.builders.monitoring.grafana_admin"

    def _init(self, **kwargs):
        j.core.tools.dir_ensure(self.DIR_BUILD)
        self.version = "7.0.3"
        self.DIR_BASE_GRAFANA = "/sandbox/grafana"
        self.DIR_INSTALL = self.DIR_BUILD + f"/grafana-{self.version}"

    @builder_method()
    def clean(self):
        """
        kosmos 'j.builders.monitoring.grafana_admin.clean()'
        :param install:
        :return:
        """

        C = """

        set -ex

        rm -rf "/sandbox/grafana"
        rm {DIR_BIN}/grafana-server
        rm {DIR_BIN}/grafana-cli
        rm -rf {DIR_BUILD}
        """
        self._execute(C)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def build(self, reset=False):

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            j.core.tools.dir_ensure(self.DIR_BUILD)
            C = f"""
            cd {self.DIR_BUILD}
            wget https://dl.grafana.com/oss/release/grafana-{self.version}.linux-amd64.tar.gz
            tar -zxvf grafana-{self.version}.linux-amd64.tar.gz
            """
            j.sal.process.execute(C)
        else:
            raise j.exceptions.Base("platform not supported")

    @builder_method()
    def install(self, reset=False):
        j.core.tools.dir_ensure(self.DIR_BUILD)
        j.builders.tools.copyTree(f"{self.DIR_BUILD}/grafana-{self.version}", dest=self.DIR_BASE, recursive=True)

        j.builders.tools.file_copy(f"{self.DIR_INSTALL}/bin/grafana-server", "{DIR_BIN}")
        j.builders.tools.file_copy(f"{self.DIR_INSTALL}/bin/grafana-cli", "{DIR_BIN}")
        j.builders.tools.file_copy(
            f"{self.DIR_INSTALL}/conf/defaults.ini", f"{self.DIR_BASE_GRAFANA}/conf/grafana_cfg.ini"
        )

        C = f"""
        sed -i 's@http_port = 3000@http_port = 3005@g' {self.DIR_BASE_GRAFANA}/conf/grafana_cfg.ini
        sed -i 's@root_url = %(protocol)s://%(domain)s:%(http_port)s/@root_url = %(protocol)s://%(domain)s:%(http_port)s/grafana/@g' {self.DIR_BASE_GRAFANA}/conf/grafana_cfg.ini
        sed -i 's@allow_embedding = false@allow_embedding = true@g' {self.DIR_BASE_GRAFANA}/conf/grafana_cfg.ini
        """
        j.sal.process.execute(C)
