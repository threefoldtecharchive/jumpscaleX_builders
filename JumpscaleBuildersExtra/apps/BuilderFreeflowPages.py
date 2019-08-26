from Jumpscale import j
import textwrap

builder_method = j.builders.system.builder_method


class BuilderFreeflowPages(j.baseclasses.builder):

    __jslocation__ = "j.builders.apps.freeflowpages"

    @builder_method()
    def install(self, reset=False, humhub_version="1.3.13"):
        if self._done_check("install") and reset is False:
            return
        self.HUMHUB_VERSION = humhub_version
        self.HUMHUB_PATH = "/var/www/html/humhub"
        self.profile.env_set("DEBIAN_FRONTEND", "noninteractive")
        j.builders.system.package.install(["lamp-server^"])
        j.builders.system.package._apt_wait_free()
        j.builders.system.package.install(
            ["php-curl", "php-gd", "php-mbstring", "php-intl", "php-zip", "php-ldap", "php-apcu", "php-sqlite3"]
        )
        j.builders.tools.file_download(
            "https://www.humhub.org/en/download/package/humhub-{0}.tar.gz".format(self.HUMHUB_VERSION),
            "/var/www/html/humhub-{0}.tar.gz".format(self.HUMHUB_VERSION),
        )
        j.builders.tools.file_expand(
            "/var/www/html/humhub-{0}.tar.gz".format(self.HUMHUB_VERSION), self.HUMHUB_PATH, removeTopDir=True
        )
        sql_init_script = """
        /etc/init.d/mysql start
        mysql -e "CREATE DATABASE humhub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        mysql -e "GRANT ALL ON humhub.* TO 'humhub'@'localhost' IDENTIFIED BY 'Hum_flist_hubB';"
        mysql -e "FLUSH PRIVILEGES;"
        """
        j.builders.tools.execute(sql_init_script)
        j.sal.fs.chmod("/var/www", 0o775)
        j.sal.fs.chown("/var/www", "www-data", "www-data")
        self._done_set("install")

    @builder_method()
    def sandbox(self, dest_path="/tmp/package/freeflow", reset=False, zhub_client=None, create_flist=False):
        # dest_path = self.tools.replace(dest_path,args={"NAME":self.__class__.NAME})
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """

        self.bins = [
            "/usr/bin/mysql",
            "/usr/sbin/mysqld",
            "/usr/bin/mysql_install_db",
            "/usr/bin/my_print_defaults",
            "/usr/bin/resolveip",
            "/usr/sbin/apache2",
            "/usr/sbin/apachectl",
            "/usr/sbin/a2enconf",
            "/usr/sbin/a2enmod",
            "/usr/sbin/a2dismod",
            "/usr/bin/php",
        ]
        for bin_name in self.bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = j.sal.fs.joinPaths(dest_path, j.core.dirs.BINDIR[1:])
            j.builders.tools.dir_ensure(dir_dest)
            j.sal.fs.copyFile(dir_src, dir_dest)
        lib_dest = j.sal.fs.joinPaths(dest_path, "sandbox/lib")
        j.builders.tools.dir_ensure(lib_dest)
        for bin in self.bins:
            j.tools.sandboxer.libs_sandbox(bin, lib_dest, exclude_sys_libs=False)
        self.share = ["/usr/share/mysql"]
        for mysqlshare in self.share:
            share_dest = j.sal.fs.joinPaths(dest_path, "sandbox/share/mysql")
            j.builders.tools.dir_ensure(share_dest)
            self.tools.copyTree(mysqlshare, share_dest)

        apache_dir = ["/etc/apache2", "/usr/lib/apache2", "/etc/php", "/usr/lib/php", "/var/lib/php"]
        for dir in apache_dir:
            relative_dir = dir.strip("/")
            dest_dir = j.sal.fs.joinPaths(dest_path, "sandbox", relative_dir)
            j.builders.tools.dir_ensure(dest_dir)
            self.tools.copyTree(dir, dest_dir, keepsymlinks=True)

        copy_php_share_script = """
        mkdir -p /tmp/package/freeflow/sandbox/usr/share/php
        cp -r /usr/share/php7.2-* /tmp/package/freeflow/sandbox/usr/share/php
        cd /usr/lib/x86_64-linux-gnu/
        cp -p libzip.so.4 libexpat.so* libfontconfig.so.1 libfreetype.so.6 libgd.so.3 libjbig.so.0 libjpeg.so.8 libpng16.so.16 libssl.so* libtiff.so.5 libwebp.so.6 libX11.so.6 libXau.so.6 libxcb.so.1 libXdmcp.so.6 libXpm.so.4 /tmp/package/freeflow/sandbox/lib
        chmod +x -R /tmp/package/freeflow/sandbox/lib
        cd 
        """
        j.builders.tools.execute(copy_php_share_script)
        startup_file = (
            "/sandbox/code/github/threefoldtech/jumpscaleX_coreJumpscale/builder/apps/templates/freeflow_startup.toml"
        )
        startup = j.sal.fs.readFile(startup_file)
        startup_dest = j.sal.fs.joinPaths(dest_path, ".startup.toml")
        j.builders.tools.file_ensure(startup_dest)
        j.builders.tools.file_write(startup_dest, startup)
        apache_file = "/sandbox/code/github/threefoldtech/jumpscaleX_coreJumpscale/builder/apps/templates/freeflow_apache_prepare.sh"
        apache_conf = j.sal.fs.readFile(apache_file)
        apache_conf_dest = j.sal.fs.joinPaths(dest_path, ".apache_prepare.sh")
        j.builders.tools.file_ensure(apache_conf_dest)
        j.builders.tools.file_write(apache_conf_dest, apache_conf)
        self._done_set("sandbox")
        if create_flist:
            # import ipdb; ipdb.set_trace()
            print(self._flist_create(zhub_client))

    def stop(self):
        stop_script = """
        /etc/init.d/apache2 stop
        /etc/init.d/mysql stop
        """
        j.builders.tools.execute(stop_script)

    def start(self):
        start_script = """
        if [ ! -f /etc/apache2/conf-available/fqdn.conf ]; then
        echo "ServerName localhost"  > /etc/apache2/conf-available/fqdn.conf
        a2enconf fqdn
        fi
        /etc/init.d/mysql start
        /etc/init.d/apache2 start
        """
        j.builders.tools.execute(start_script)

    def test(self):
        self.stop()
        self.start()
