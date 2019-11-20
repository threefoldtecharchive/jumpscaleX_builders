import textwrap

from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderGitea(BuilderGolangTools):
    __jslocation__ = "j.builders.apps.gitea"

    def _init(self, **kwargs):
        super()._init()
        # set needed paths
        self.GITEAPATH = self._replace("{DIR_GO_PATH}/src/code.gitea.io/gitea")
        self.CUSTOM_PATH = "%s/custom" % self.GITEAPATH
        # app.ini will be bundled with the binary
        self.INIPATH = "%s/custom/conf/app.ini" % self.DIR_GO_PATH_BIN

    @builder_method()
    def build(self):
        """Build Gitea with itsyou.online authentication"""
        self._installDeps()
        self.get("code.gitea.io/gitea", install=False)

        # change branch from master to gigforks/iyo_integration
        _, out, _ = self._execute("cd {GITEAPATH} && git remote")
        if "gigforks" not in out:
            self._execute(
                """cd {GITEAPATH}
                git remote add gigforks https://github.com/gigforks/gitea
                """
            )

        self._execute("cd {GITEAPATH} && git fetch gigforks && git checkout gigforks/iyo_integration")

        # gitea-custom is needed to replace the default gitea custom
        j.clients.git.pullGitRepo("https://github.com/incubaid/gitea-custom.git", branch="master")
        if self.tools.exists(self.CUSTOM_PATH) and not self.tools.file_is_link(self.CUSTOM_PATH):
            self.tools.dir_remove(self.CUSTOM_PATH)

        self.tools.file_link(
            source=j.core.tools.text_replace("{DIR_BASE}/code/github/incubaid/gitea-custom"),
            destination=self.CUSTOM_PATH,
        )

        # build gitea (will be stored in self.GITEAPATH/gitea)
        self._execute('cd {GITEAPATH} && TAGS="bindata" make generate build')

    def _installDeps(self):
        """Install gitea deps

        sys packages: git-core, gcc, golang
        db: postgresql
        """
        j.builders.system.package.mdupdate()
        j.builders.system.package.ensure("git-core")
        j.builders.system.package.ensure("gcc")
        j.builders.runtimes.go.install()
        j.builders.db.psql.install()

    def write_ini_config(self, path):
        # Configure Database
        config = """
        RUN_MODE = prod
        [database]
        DB_TYPE  = postgres
        HOST     = localhost:5432
        NAME     = gitea
        USER     = postgres
        PASSWD   = postgres
        SSL_MODE = disable
        PATH     = data/gitea.db
        [security]
        INSTALL_LOCK = true
        [log]
        MODE      = file
        LEVEL     = Info
        """

        config = textwrap.dedent(config)
        self._dir_ensure(j.sal.fs.getDirName(path))
        self._write(path, config)

    @builder_method()
    def configure(self, org_client_id, org_client_secret):
        """Configure gitea, db, iyo"""
        self.write_ini_config(self.INIPATH)

        try:
            self.stop()
        except j.exceptions.RuntimeError:
            # not started
            pass

        j.builders.db.psql.start()

        _, out, _ = self._execute("sudo -u postgres {DIR_BIN}/psql -l")
        if "gitea" not in out:
            self._execute("sudo -u postgres {DIR_BIN}/psql -c 'create database gitea;'")
        self.start()

        # TODO:*3 would have been cleaner to use std postgresql client & do the query, this is super cumbersome
        cfg = """
        {{\\"Provider\\":\\"itsyou.online\\",\\"ClientID\\":\\"%s\\",\\"ClientSecret\\":\\"%s\\",\\"OpenIDConnectAutoDiscoveryURL\\":\\"\\",\\"CustomURLMapping\\":null}}
        """ % (
            org_client_id,
            org_client_secret,
        )

        cmd = """
        "INSERT INTO login_source (type, name, is_actived, cfg, created_unix, updated_unix)
        VALUES (6, 'Itsyou.online', TRUE,
                '{cfg}',
                extract('epoch' from CURRENT_TIMESTAMP) , extract('epoch' from CURRENT_TIMESTAMP))
        ON CONFLICT (name) DO UPDATE set cfg = '{cfg}';"
        """.format(
            cfg=cfg
        )
        cmd = cmd.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        self._execute("sudo -u postgres {DIR_BIN}/psql gitea -c %s" % cmd)

    @builder_method()
    def install(self):
        # copy the binary with bundled assets using bindata to $GOPATH/bin
        self._copy("{GITEAPATH}/gitea", "{DIR_GO_PATH}/bin/gitea")

    @property
    def startup_cmds(self):
        cmd = j.servers.startupcmd.get("gitea", "gitea web", path=j.core.tools.text_replace("{DIR_BASE}/bin"))
        return j.builders.db.psql.startup_cmds + [cmd]

    @builder_method()
    def sandbox(self):
        j.builders.db.psql.sandbox()

        # add certs
        dir_dest = self._joinpaths(self.DIR_SANDBOX, "etc/ssl/certs/")
        self._dir_ensure(dir_dest)
        self._copy("{DIR_BASE}/cfg/ssl/certs", dir_dest)

        # gitea bin
        self._dir_ensure("{DIR_SANDBOX}/sandbox/bin")
        self._copy("{DIR_GO_PATH}/bin/gitea", "{DIR_SANDBOX}/sandbox/bin/gitea")

        # startup files
        templates_dir = self._joinpaths(j.sal.fs.getDirName(__file__), "templates")
        postgres_init_script = self._replace("{DIR_SANDBOX}/sandbox/bin/gitea_postgres_init.sh")
        gitea_init_script = self._replace("{DIR_SANDBOX}/sandbox/bin/gitea_init.sh")
        gitea_startup = self._replace("{DIR_SANDBOX}/.startup.toml")
        self._copy(self._joinpaths(templates_dir, "gitea_postgres_init.sh"), postgres_init_script)
        self._copy(self._joinpaths(templates_dir, "gitea_init.sh"), gitea_init_script)
        self._copy(self._joinpaths(templates_dir, "gitea_startup.toml"), gitea_startup)

        # init config
        custom_dir = self._replace("{DIR_SANDBOX}/sandbox/bin/custom/conf")
        self.write_ini_config("%s/app.ini" % custom_dir)
