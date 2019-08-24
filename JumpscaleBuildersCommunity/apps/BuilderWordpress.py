from Jumpscale import j
import textwrap
import time


class BuilderWordpress(j.builders.system._BaseClass):
    NAME = "wordpress"

    def _init(self, **kwargs):
        self.user = "wordpress"

    def build(self, reset=False):
        """
        build wordpress
        1- install php
        2- install mysql
        3- install caddy
        4- install wp-cli (a cli tool for wordpress)
        """
        if self._done_check("build", reset):
            return
        # 1- install php
        j.builders.system.package.ensure(
            "php7.0-fpm, php7.0-mysql, php7.0-curl, php7.0-gd, php7.0-mbstring, php7.0-mcrypt, php7.0-xml, php7.0-xmlrpc"
        )

        # 2- install mysql
        j.builders.db.mariadb.install(start=True)

        # 3- install caddy
        j.builders.web.caddy.install(plugins=["iyo"])

        # 4- nstall wp-cli
        url = "https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
        cli_path = "/usr/local/bin/wp"
        cli_path = self._replace(cli_path)
        j.builders.tools.file_download(url=url, to=cli_path, overwrite=True, retry=3, timeout=0, removeTopDir=False)

        j.builders.executor.execute("chmod +x %s" % cli_path)
        if not j.builders.system.user.check(self.user):
            j.builders.system.user.create(self.user)
        self._done_set("build")

    def install(
        self,
        path,
        url,
        title,
        admin_user,
        admin_password,
        admin_email,
        db_name="wordpress",
        db_user="wordpress",
        db_password="wordpress",
        port=8090,
        plugins=None,
        theme=None,
        reset=False,
    ):
        """install 

        @param path: a path to setup wordpress to, Note that all content in this path will be deleted
        @param url: website's url
        @param title: website's title
        @param admin_user: admin username
        @param admin_password: admin password
        @param admin_email: admin email
        @param db_name: (default = Wordpress) database name to be used in wordpress
        @param db_user: (default = wordpress) database user 
        @param db_password: (default = wordpress) database password, Very important to change with a strong password
        @param port: (default = 8090) the host port
        @param plugins: (default = None) list of plugin names you want to install, Acceps plugins slugs from 
        wordpress plugins directory: https://wordpress.org/plugins/
        @param reset: (default = False) if True build will start again even if it was already built
        """
        if self._done_check("install", reset):
            return
        self.build(reset=reset)

        # create a database
        j.builders.db.mariadb.sql_execute(
            None, "CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % db_name
        )
        # create a new super user for this database
        j.builders.db.mariadb.admin_create(db_user, db_password)

        j.core.tools.dir_ensure(path)
        j.sal.process.execute("chown {0}:{0} {1}".format(self.user, path))

        # start server
        cfg = """
        :{} {{
           	bind 0.0.0.0
        	root {}
           	fastcgi / /var/run/php/php7.0-fpm.sock php
        }}
        """.format(
            port, path
        )
        j.builders.web.caddy.add_website("wordpress", cfg)

        j.builders.executor.execute("rm -rf {}/*".format(path))
        # download wordpress
        j.builders.executor.execute("sudo -u {} -i -- wp core download --path={}".format(self.user, path))

        # configure wordpress
        configure_command = """
        sudo -u {user} -i -- wp --path={path} config create --dbname={db_name} --dbuser='{db_user}' --dbpass='{db_password}' 
        """.format(
            user=self.user, db_name=db_name, db_user=db_user, db_password=db_password, path=path
        )
        j.builders.executor.execute(configure_command)

        # install wordpress
        install_command = """
        sudo -u {user} -i -- wp  --path={path} core install --url='{url}' --title='{title}' --admin_user='{admin_user}' --admin_password='{admin_password}' --admin_email='{admin_email}'
        """.format(
            user=self.user,
            url=url,
            title=title,
            admin_user=admin_user,
            admin_password=admin_password,
            admin_email=admin_email,
            path=path,
        )
        j.builders.executor.execute(install_command)

        # install themes
        self.install_theme(path, theme)

        # install plugins
        self.install_plugins(path, plugins, True)

        # allow plugins upload from ui without ftp and increase allowed file size
        configs = {"FS_METHOD": "direct", "WP_MEMORY_LIMIT": "256M"}
        self.add_config(path, configs)

        # allow file uploads
        cmd = """
        sudo chown -R www-data:www-data {path}/wp-content
        """.format(
            path=path
        )
        j.builders.executor.execute(cmd)

        self._done_set("install")

    def install_theme(self, path, theme):
        if theme:
            themes_command = """
            sudo -u {} -i -- wp --path={} theme install {} --activate
            """.format(
                self.user, path, theme
            )
            j.sal.process.execute(themes_command, die=False)

    def install_plugins(self, path, plugins, activate=False):
        if not plugins:
            plugins = []

        activate_cmd = ""
        if activate:
            activate_cmd = "--activate"

        for plugin in plugins:
            plugins_command = """
            sudo -u {} -i -- wp --path={} plugin install {} {}
            """.format(
                self.user, path, plugin, activate_cmd
            )
            j.sal.process.execute(plugins_command, die=False)

    def add_config(self, path, config):
        """add constants to wordpress config
        
        Arguments:
            config {Dict} -- constances to be added
        """
        for item in config.items():
            command = """
            sudo -u {} -i -- wp --path={} config set {} {} --type="constant"
            """.format(
                self.user, path, item[0], item[1]
            )
            j.sal.process.execute(command)

    def download_backup(self, path, cfg_path="/opt/cfg", dbname="wordpress"):
        """download a full packup for a wordpress website including
        1- databse dump
        2- wp files
        3- caddy configurations
        
        Arguments:
            path {STRING} -- wordpress installation path
            dbname {STRING} -- databse name
        """

        backup_path = "/tmp/backup_{}".format(str(time.time()))
        j.core.tools.dir_ensure(backup_path)
        # export database
        j.builders.db.mariadb.db_export(dbname, backup_path)
        # get wordpress files
        j.core.tools.dir_ensure(backup_path + path)
        j.builders.tools.copyTree(path, backup_path + path)
        # get get cfgs
        j.core.tools.dir_ensure(backup_path + cfg_path)
        j.builders.tools.copyTree(cfg_path, backup_path + cfg_path)

        backup_tar_name = "/tmp/backup_{}.tar.gz".format(str(time.time()))

        rc, _, _ = j.sal.process.execute("tar -czvf {} {}".format(backup_tar_name, backup_path))
        if rc == 0:
            self._log_info("Backup done successfuly")
        else:
            self._log_info("an error happened while compressing your backup")

        # clean up
        j.builders.tools.dir_remove(backup_path)
