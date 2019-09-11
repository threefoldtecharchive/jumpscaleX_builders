from Jumpscale import j
import textwrap

builder_method = j.baseclasses.builder_method


class BuilderGraphql(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.graphql"

    def _init(self, **kwargs):
        self.APP_DIR = self._replace("{DIR_BASE}/apps/graphql")

    @builder_method()
    def clean(self):
        self._remove(self.DIR_BUILD)
        self._remove(self.APP_DIR)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def build(self):
        # TODO : Build from source
        graphql_websockets_url = "https://github.com/threefoldfoundation/graphql_websockets"
        j.clients.git.pullGitRepo(
            dest=self.tools.joinpaths(self.DIR_BUILD, "graphql_websockets"), url=graphql_websockets_url, depth=1
        )

    @builder_method()
    def install(self):
        self.system.package.install("sudo")
        self.tools.copyTree(
            self.tools.joinpaths(self.DIR_BUILD, "graphql_websockets"), self.APP_DIR, deletefirst=True, createdir=True
        )

        # install graphql_ws,sanic, graphene, s
        # sanic-graphql
        cmd = self._replace(
            """
            id -u graphuser &>/dev/null || useradd graphuser --home {APP_DIR} --no-create-home --shell /bin/bash
            chown -R graphuser:graphuser {APP_DIR}
            cd {APP_DIR}
            sudo -H -u graphuser python3 -m pip install --user -r requirements.txt
        """
        )
        self._execute(cmd)

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None, flist_create=False):
        # TODO
        pass

    @property
    def startup_cmds(self):
        # j.builders.db.zdb.start()
        start_script = self._replace(
            """
        chown -R graphuser:graphuser {APP_DIR}
        cd {APP_DIR}
        sudo -H -u graphuser python3 app.py
        """
        )
        start_cmd = j.servers.startupcmd.get(self._name, cmd_start=start_script, ports=[8000])
        return [start_cmd]

    @builder_method()
    def stop(self):
        # killing the daemon
        j.servers.tmux.pane_get(self._name).kill()
        j.builders.db.zdb.stop()

    @builder_method()
    def test(self):
        if self.running():
            self.stop()
        self.start()
        assert self.running()
        self.stop()
        print("TEST OK")
