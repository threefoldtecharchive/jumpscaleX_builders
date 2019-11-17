from Jumpscale import j
import time

builder_method = j.baseclasses.builder_method


class BuilderMariadb(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.mariadb"
    PORT = "3306"

    def _init(self, **kwargs):
        # code dir
        self.code_dir = j.sal.fs.joinPaths(self.DIR_BUILD, "code")
        # self.start_cmd = """
        # useradd -r mysql
        # chown -R mysql.mysql {DATA_DIR}
        # chown -R mysql.mysql /var/run/mysqld
        # /usr/sbin/mysqld --basedir=/usr --datadir={DATA_DIR} \
        # --plugin-dir=/usr/lib/mysql/plugin --log-error=/dev/log/mysql/error.log \
        # --pid-file=/var/run/mysqld/mysqld.pid \
        # --socket=/var/run/mysqld/mysqld.sock --port={}""".format(
        #     self.PORT, DATA_DIR=self.DATA_DIR
        # )

    @builder_method()
    def build(self):
        """
        Build mariadb from source code
        """
        # install dependancies and clone repo
        url = "https://github.com/MariaDB/server"
        self.tools.dir_ensure(self.code_dir)
        self._execute("sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list")
        self.system.package.mdupdate()
        self._execute("apt-get build-dep mysql-server -y")
        self.system.package.install(["libgnutls28-dev"])
        j.builders.libs.cmake.install()
        cmd = """
        set -ex
        cd {}
        rm -rf server
        git clone {} --depth 1 --branch 10.4
        """.format(
            self.code_dir, url
        )
        self._execute(cmd)
        # build - compile the source
        build_cmd = """
        cd {}/server
        git clean -dffx
        git reset --hard HEAD
        git submodule update
        cmake . -LH
        cmake . -DCMAKE_BUILD_TYPE=Release -DWITHOUT_MROONGA=True -DWITH_EMBEDDED_SERVER=1
        make -j5
        """.format(
            self.code_dir
        )
        self._execute(build_cmd, timeout=3000)

    @builder_method()
    def clean(self):
        self._remove(self.code_dir)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def install(self):
        """
        install and configure mariadb
        Keyword Arguments:
            reset {bool} -- flag to specify whether to force install (default: {False})
        """
        j.builders.system.package.ensure("libaio1")
        j.builders.system.package.ensure("libaio-dev")

        install_cmd = """
        cd {}/server
        make install DESTDIR={DIR_BASE}
        """.format(
            self.code_dir
        )
        self._execute(install_cmd)

        script = """
        useradd -r mysql || true
        chmod 777 {DIR_BASE}/usr/local/mysql/
        chown -R mysql:mysql {DIR_BASE}/usr/local/mysql/
        cd {DIR_BASE}/usr/local/mysql/
        scripts/mysql_install_db --basedir={DIR_BASE}/usr/local/mysql \
            --datadir={DIR_BASE}/usr/local/mysql/data
        chown -R mysql:mysql {DIR_BASE}/usr/local/mysql/
        """
        self._execute(script)

    @property
    def startup_cmds(self):

        cmd = """
        {DIR_BASE}/usr/local/mysql/bin/mysqld --datadir={DIR_BASE}/usr/local/mysql/data\
            --basedir={DIR_BASE}/usr/local/mysql --user=mysql
        """
        cmd_start = cmd

        cmd = j.servers.startupcmd.get("mysqld", cmd_start=cmd_start)
        return [cmd]

    @builder_method()
    def stop(self):
        j.sal.process.killProcessByName("mysqld")

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """

        sandbox_dir = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(sandbox_dir)
        install_cmd = """
        cd {}/server
        make install DESTDIR={}
        """.format(
            self.code_dir, sandbox_dir
        )
        self._execute(install_cmd)

        mysql_bin_content = j.sal.fs.listFilesAndDirsInDir(j.sal.fs.joinPaths(sandbox_dir, "usr/local/mysql/bin"))
        for bin_src in mysql_bin_content:
            j.tools.sandboxer.libs_clone_under(bin_src, self.DIR_SANDBOX)

        # startup.toml
        templates_dir = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates")
        startup_path = self._replace("{DIR_SANDBOX}/.startup.toml")
        self._copy(self.tools.joinpaths(templates_dir, "mariadb_startup.toml"), startup_path)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()
        self.start()
        assert self.running()
        self.stop()
        print("TEST OK")


class MariaClient:
    def init(self, **kwargs):
        """Initialize the data directory
        """
        cmd = "mysql_install_db"
        j.sal.process.execute(cmd)

    def db_export(self, dbname, targetdir):
        """export specified database

        Arguments:
            db_name {string} -- name of the database to be exported
            target_dir    {string} -- dir to which db will be exported to
        """

        target = j.sal.fs.joinPaths(targetdir, "datadump-" + str(int(time.time())) + ".sql")
        cmd = "mysqldump {} > {}".format(dbname, target)
        j.sal.process.execute(cmd)

    def db_import(self, dbname, sqlfile):
        """export specified database

        Arguments:
            dbname   {string} -- name of the database that sqlfile will be imported to
            sqlfile  {string} -- sqlfile path to be imported
        """
        self._create_db(dbname)
        cmd = "mysql {dbname} < {sqlfile}".format(dbname=dbname, sqlfile=sqlfile)
        j.sal.process.execute(cmd)

    def user_create(self, username, password=""):
        """creates user with no rights

        Arguments:
            username   {string} -- username to be created
            password   {string} -- if provided will be the creted user password
        """
        if password:
            password = "IDENTIFIED BY '{password}'".format(password=password)
        cmd = 'echo "CREATE USER {username}@localhost {password}"| mysql'.format(username=username, password=password)
        j.sal.process.execute(cmd, die=False)

    def admin_create(self, username, password=""):
        """creates user with all rights

        Arguments:
            username   {string} -- username to be created
            password   {string} -- if provided will be the creted user password
        """

        self.user_create(username, password=password)
        cmd = "echo \"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'localhost' WITH GRANT OPTION;\" | mysql".format(
            username=username
        )
        j.sal.process.execute(cmd, die=False)

    def sql_execute(self, dbname, sql):
        """[summary]

        Arguments:
            dbname {string} -- database name that query will run against
            sql    {string} -- sql query to be run
        """
        if not dbname:
            dbname = ""
        cmd = 'mysql -e "{}" {}'.format(sql, dbname)
        j.sal.process.execute(cmd)

    def user_db_access(self, username, dbname):
        """give use right to this database (fully)
        username   {string} -- username to be granted the access
        dbname     {string} -- database name to which access would be granted
        """

        cmd = 'echo "GRANT ALL PRIVILEGES ON {dbname}.* TO {username}@localhost WITH GRANT OPTION;" | mysql'.format(
            dbname=dbname, username=username
        )
        j.sal.process.execute(cmd, die=False)

    def _create_db(self, dbname):
        cmd = 'echo "CREATE DATABASE {dbname}" | mysql'.format(dbname=dbname)
        j.sal.process.execute(cmd, die=False)

