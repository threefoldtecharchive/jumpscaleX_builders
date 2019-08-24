from Jumpscale import j


class BuilderGrafana(j.builders.system._BaseClass):

    NAME = "grafana-server"

    def build(self, reset=False):

        if reset is False and self.isInstalled():
            return

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            C = """
            cd {DIR_TEMP}
            wget https://grafanarel.s3.amazonaws.com/builds/grafana_3.1.1-1470047149_amd64.deb
            sudo apt-get install -y adduser libfontconfig
            sudo dpkg -i grafana_3.1.1-1470047149_amd64.deb

            """
            j.sal.process.execute(C, profile=True)
        else:
            raise j.exceptions.Base("platform not supported")

    def install(self, start=False, influx_addr="127.0.0.1", influx_port=8086, port=3000):
        j.core.tools.dir_ensure("{DIR_BIN}")
        j.builders.tools.file_copy("/usr/sbin/grafana*", dest="{DIR_BIN}")

        j.core.tools.dir_ensure("{DIR_BASE}/apps/grafana")
        j.builders.tools.file_copy("/usr/share/grafana/", "{DIR_BASE}/apps/", recursive=True)

        if j.builders.tools.file_exists("/usr/share/grafana/conf/defaults.ini"):
            cfg = j.core.tools.file_text_read("/usr/share/grafana/conf/defaults.ini")
        else:
            cfg = j.core.tools.file_text_read("{DIR_TEMP}/cfg/grafana/conf/defaults.ini")
        j.sal.fs.writeFile("{DIR_BASE}/cfg/grafana/grafana.ini", cfg)

        if start:
            self.start(influx_addr, influx_port, port)

    def start(self, influx_addr="127.0.0.1", influx_port=8086, port=3000):

        cmd = "{DIR_BIN}/grafana-server --config={DIR_BASE}/cfg/grafana/grafana.ini\n"
        cmd = self._replace(cmd)
        j.sal.fs.writeFile("/opt/jumpscale/bin/start_grafana.sh", cmd, 777, replaceArgs=True)
        j.builders.system.process.kill("grafana-server")
        pm = j.builders.system.processmanager.get()
        pm.ensure("grafana-server", cmd=cmd, env={}, path="{DIR_BASE}/apps/grafana")
        grafanaclient = j.clients.grafana.get(
            url="http://%s:%d" % (j.builders.tools.executor.addr, port), username="admin", password="admin"
        )
        data = {
            "type": "influxdb",
            "access": "proxy",
            "database": "statistics",
            "name": "influxdb_main",
            "url": "http://%s:%u" % (influx_addr, influx_port),
            "user": "admin",
            "password": "passwd",
            "default": True,
        }
        import time
        import requests

        now = time.time()
        while time.time() - now < 10:
            try:
                grafanaclient.addDataSource(data)
                if not grafanaclient.listDataSources():
                    continue
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                pass
