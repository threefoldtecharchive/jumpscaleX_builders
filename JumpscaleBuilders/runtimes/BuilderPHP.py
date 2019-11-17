from Jumpscale import j
import textwrap
from copy import deepcopy

builder_method = j.baseclasses.builder_method

compileconfig = {}
compileconfig["enable_mbstring"] = True
compileconfig["with_zip"] = True
compileconfig["enable_gd"] = True
compileconfig["with_curl"] = True  # apt-get install libcurl4-openssl-dev libzip-dev
compileconfig["with_libzip"] = False
compileconfig["with_zlib"] = True
compileconfig["with_openssl"] = True
compileconfig["enable_fpm"] = True
compileconfig["prefix"] = j.core.tools.text_replace("{DIR_BASE}")
compileconfig["exec_prefix"] = j.core.tools.text_replace("{DIR_BASE}")
compileconfig["with_mysqli"] = True
compileconfig["with_pdo_mysql"] = True
compileconfig["with_mysql_sock"] = "/var/run/mysqld/mysqld.sock"


class BuilderPHP(j.baseclasses.builder):

    __jslocation__ = "j.builders.runtimes.php"

    @builder_method()
    def build(self, **config):
        """
        kosmos 'j.builders.runtimes.php.build()'
        :param config:
        :return:
        """
        # install required packages
        pkgs = "curl libxml2-dev libpng-dev libcurl4-openssl-dev libzip-dev zlibc zlib1g zlib1g-dev \
        libmysqld-dev libmysqlclient-dev re2c bison bzip2 build-essential libaprutil1-dev libapr1-dev \
        openssl pkg-config libssl-dev file libreadline7 libreadline-dev libzip4 autoconf libtool libsqlite3-dev"
        self.system.package.install(pkgs)

        # install oniguruma
        C = """
        cd {DIR_BUILD}
        rm -rf oniguruma
        git clone https://github.com/kkos/oniguruma.git --depth 1
        cd oniguruma
        autoreconf -vfi
        ./configure --prefix={DIR_BASE}
        make
        make install
        """
        self._execute(C)

        # clone php-src repo
        C = """
        cd {DIR_BUILD}
        rm -rf php-src
        git clone https://github.com/php/php-src.git --depth 1
        """
        self._execute(C)

        # configure arguments
        compileconfig["with_apxs2"] = self._replace("{DIR_APPS}/apache2/bin/apxs")
        buildconfig = deepcopy(compileconfig)
        buildconfig.update(config)  # should be defaultconfig.update(config) instead of overriding the explicit ones.

        # check for apxs2 binary if it's valid.
        apxs = buildconfig["with_apxs2"]
        if not self.tools.exists(apxs):
            buildconfig.pop("with_apxs2")

        args_string = ""
        for k, v in buildconfig.items():
            k = k.replace("_", "-")
            if v is True:
                args_string += " --{k}".format(k=k)
            else:
                args_string += " --{k}={v}".format(k=k, v=v)
        args_string = self._replace(args_string)

        # build php
        C = (
            """
        cd {DIR_BUILD}/php-src
        ./buildconf
        export PKG_CONFIG_PATH={DIR_BASE}/lib/pkgconfig/
        ./configure %s
        make
        """
            % args_string
        )
        self._execute(C, timeout=1000)

        # check if we need an php accelerator: https://en.wikipedia.org/wiki/List_of_PHP_accelerators

    @builder_method()
    def install(self):
        fpm_default_conf = """\
        include={DIR_BASE}/etc/php-fpm.d/*.conf
        """
        fpm_www_conf = """\
        ;nobody Start a new pool named 'www'.
        [www]

        ;prefix = /path/to/pools/$pool

        user =  www-data
        group = www-data

        listen = /var/run/php-fpm.sock
        ;listen.allowed_clients = 127.0.0.1
        listen.owner = www-data
        listen.group = www-data

        pm = dynamic
        pm.max_children = 5
        pm.start_servers = 2
        pm.min_spare_servers = 1
        pm.max_spare_servers = 3
        """
        fpm_default_conf = textwrap.dedent(fpm_default_conf)
        fpm_www_conf = textwrap.dedent(fpm_www_conf)
        # make sure to save that configuration file ending with .conf under php/etc/php-fpm.d/www.conf
        self._execute("cd {DIR_BUILD}/php-src && make install")

        self.tools.dir_ensure(self._replace("{{DIR_BASE}/etc/php-fpm.d"))
        fpm_default_conf = self._replace(fpm_default_conf)
        fpm_www_conf = self._replace(fpm_www_conf)
        self._write(path=j.core.tools.text_replace("{DIR_BASE}/etc/php-fpm.conf"), txt=fpm_default_conf)
        self._write(path=j.core.tools.text_replace("{DIR_BASE}/etc/php-fpm.d/www.conf"), txt=fpm_www_conf)

        php_tmp_path = self._replace("{DIR_BUILD}/php-src")
        php_app_path = self._replace(j.core.tools.text_replace("{DIR_BASE}"))
        self._copy(
            self.tools.joinpaths(php_tmp_path, "php.ini-development"), self.tools.joinpaths(php_app_path, "php.ini")
        )

        # It is important that we prevent Nginx from passing requests to the PHP-FPM backend if the file does not exists,
        # allowing us to prevent arbitrarily script injection.
        # We can fix this by setting the cgi.fix_pathinfo directive to 0 within our php.ini file.
        C = """
        sed -i 's/;cgi.fix_pathinfo=1/;cgi.fix_pathinfo=0/g' {php_app_path}/php.ini
        """.format(
            php_app_path=php_app_path
        )
        self._execute(C)

    @property
    def startup_cmds(self):
        cmd = j.core.tools.text_replace("{DIR_BASE}/sbin/php-fpm -F -y {DIR_BASE}/etc/php-fpm.conf")  # foreground
        cmds = [j.servers.startupcmd.get(name=self._name, cmd_start=cmd)]
        return cmds

    def stop(self):
        super().stop()
        j.sal.process.killProcessByName(self._name)

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        # bins
        bins = ["phar", "phar.phar", "php", "php-cgi", "php-config", "phpdbg", "phpize"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(self.DIR_SANDBOX, j.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        # sbin
        sbin_src = j.core.tools.text_replace("{DIR_BASE}/sbin/php-fpm")
        sbin_dest = self.tools.joinpaths(self.DIR_SANDBOX, sbin_src[1:])
        self._copy(sbin_src, sbin_dest)

        # libs
        lib_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

        # libs
        libs_src = j.core.tools.text_replace("{DIR_BASE}/lib/php")
        libs_dest = self.tools.joinpaths(self.DIR_SANDBOX, libs_src[1:])
        self.tools.dir_ensure(libs_dest)
        self._copy(libs_src, libs_dest)

        # include
        include_src = j.core.tools.text_replace("{DIR_BASE}/include/php")
        include_dest = self.tools.joinpaths(self.DIR_SANDBOX, include_src[1:])
        self.tools.dir_ensure(include_dest)
        self._copy(include_src, include_dest)

        # php
        php_src = j.core.tools.text_replace("{DIR_BASE}/php")
        php_dest = self.tools.joinpaths(self.DIR_SANDBOX, php_src[1:])
        self.tools.dir_ensure(php_dest)
        self._copy(php_src, php_dest)

        # configs
        default_conf = j.core.tools.text_replace("{DIR_BASE}/etc/php-fpm.conf")
        fpm_www_conf = j.core.tools.text_replace("{DIR_BASE}/etc/php-fpm.d/www.conf")
        default_conf_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/etc/")
        www_conf_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/etc/php-fpm.d")
        self.tools.dir_ensure(www_conf_dest)
        self._copy(default_conf, default_conf_dest)
        self._copy(fpm_www_conf, www_conf_dest)

        # php.ini
        phpini_src = j.core.tools.text_replace("{DIR_BASE}/php.ini")
        phpini_dest = self.tools.joinpaths(self.DIR_SANDBOX, phpini_src[1:])
        self._copy(phpini_src, phpini_dest)

    def test(self, name=""):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self._test_run(name=name, obj_key="test_main")

    def clean(self):
        self._remove("{DIR_BUILD}/php-src")
        self._remove("{DIR_BUILD}/oniguruma")
