from Jumpscale import j

builder_method = j.builders.system.builder_method
import time


class BuilderPostgresql(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.psql"

    def _init(self, **kwargs):
        self.DOWNLOAD_DIR = self.tools.joinpaths(self.DIR_BUILD, "build")
        self.DATA_DIR = self._replace("{DIR_VAR}/psql/data")

    @builder_method()
    def build(self):
        postgres_url = "https://ftp.postgresql.org/pub/source/v9.6.13/postgresql-9.6.13.tar.gz"
        j.builders.tools.file_download(postgres_url, to=self.DOWNLOAD_DIR, overwrite=False, expand=True)
        j.builders.system.package.ensure(["build-essential", "zlib1g-dev", "libreadline-dev", "sudo"])

        cmd = self._replace(
            """
            cd {DOWNLOAD_DIR}/postgresql-9.6.13
            ./configure --prefix={DIR_BASE}
            make
        """
        )
        self._execute(cmd)

    @builder_method()
    def install(self, port=5432):
        """
        kosmos 'j.builders.db.postgres.install()'
        kosmos 'j.builders.db.postgres.stop()'

        :param port:
        :return:
        """
        """
        :param port: 
        :return: 
        """
        cmd = self._replace(
            """
            cd {DOWNLOAD_DIR}/postgresql-9.6.13
            make install
        """
        )
        self._execute(cmd)

        self._remove(self.DATA_DIR)

        self.init()

    def init(self):

        if not self.tools.group_exists("postgres"):
            self._execute(
                'adduser --system --quiet --home {DIR_BASE} --no-create-home \
                --shell /bin/bash --group --gecos "PostgreSQL administrator" postgres'
            )

        c = self._replace(
            """
            cd {DIR_BASE}
            mkdir -p log
            mkdir -p {DATA_DIR}
            chown -R postgres {DATA_DIR}
            sudo -u postgres {DIR_BIN}/initdb -D {DATA_DIR} -E utf8 --locale=en_US.UTF-8
        """
        )
        self._execute(c)

    @property
    def startup_cmds(self):

        if not self._exists("{DATA_DIR}"):
            self.init()

        # run the db with the same user when running odoo server
        cmd = j.servers.startupcmd.get("postgres")
        cmd.cmd_start = self._replace("sudo -u postgres  {DIR_BIN}/postgres -D {DATA_DIR}")
        cmd.cmd_stop = "sudo -u postgres {DIR_BIN}/pg_ctl stop -D {DATA_DIR}"
        cmd.ports = [5432]
        cmd.path = "/sandbox/bin"
        return cmd

    def start(self):
        """
        kosmos 'j.builders.db.postgres.start()'
        :return:
        """
        self.startup_cmds.start()
        time.sleep(1)

    def test(self):
        """
        kosmos 'j.builders.db.postgres.test()'
        :return:
        """
        self.stop()
        self.start()

        _, response, _ = self._execute("pg_isready -h localhost -p 5432", showout=False)
        assert "accepting connections" in response

        self.stop()
        print("TEST OK")

    @builder_method()
    def sandbox(self):
        self.PACKAGE_DIR = self._replace("{DIR_SANDBOX}/sandbox")
        self.tools.dir_ensure(self.PACKAGE_DIR)
        # data dir
        self.tools.dir_ensure("%s/apps/psql/data" % self.PACKAGE_DIR)
        self._execute(
            """
            cd {DOWNLOAD_DIR}/postgresql-9.6.13
            make install DESTDIR={DIR_SANDBOX}
            """
        )

        bins_dir = self._replace("{PACKAGE_DIR}/bin")
        j.tools.sandboxer.libs_clone_under(bins_dir, self.DIR_SANDBOX)

        # startup.toml
        templates_dir = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates")
        startup_path = self._replace("{DIR_SANDBOX}/.startup.toml")
        self._copy(self.tools.joinpaths(templates_dir, "postgres_startup.toml"), startup_path)
