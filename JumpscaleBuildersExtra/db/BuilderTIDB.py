from Jumpscale import j
import requests

builder_method = j.baseclasses.builder_method


class BuilderTIDB(j.baseclasses.builder):
    """
    Installs TIDB.
    """

    __jslocation__ = "j.builders.db.tidb"

    def _init(self, **kwargs):
        self.DIR_BUILD = self._replace("{DIR_VAR}/build/tidb")

    @builder_method()
    def build(self):
        self._dir_ensure(self.DIR_BUILD)
        tidb_url = "http://download.pingcap.org/tidb-latest-linux-amd64.tar.gz"
        self.tools.file_download(tidb_url, overwrite=False, to=self.DIR_BUILD, expand=True, removeTopDir=True)

    @builder_method()
    def install(self):
        """
        install, move files to appropriate places, and create relavent configs
        """
        self._copy("{DIR_BUILD}/bin/", "{DIR_BIN}")

    @property
    def startup_cmds(self):
        cmds = list()

        self.DIR_VAR = self._replace("{DIR_VAR}")
        data_dir = self._joinpaths(self.DIR_VAR, "pd")
        self._dir_ensure(data_dir)
        pd_cmd = "pd-server --data-dir={data_dir}".format(data_dir=data_dir)
        cmds.append(j.servers.startupcmd.get(name="pd", cmd_start=pd_cmd))

        store_dir = self._joinpaths(self.DIR_VAR, "tikv")
        self._dir_ensure(store_dir)
        kv_cmd = "tikv-server --pd='127.0.0.1:2379' --store={store_dir}".format(store_dir=store_dir)
        cmds.append(j.servers.startupcmd.get(name="kv", cmd_start=kv_cmd))

        ti_cmd = "tidb-server --path='127.0.0.1:2379' --store=tikv"
        cmds.append(j.servers.startupcmd.get(name="ti", cmd_start=ti_cmd))
        return cmds

    @builder_method()
    def sandbox(self):
        bin_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox")
        self._dir_ensure(bin_dest)
        self._copy("{DIR_BUILD}/bin/", bin_dest)

    @builder_method()
    def clean(self):
        self._remove(self.DIR_BUILD)
        self._remove(self.DIR_SANDBOX)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        pid = j.sal.process.getProcessPid(self._name)
        assert pid is not []
        response = requests.get("http://127.0.0.1:10080/status")
        assert response.status_code == requests.codes.ok
        self.stop()

        print("TEST OK")
