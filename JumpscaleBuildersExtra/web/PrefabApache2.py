from Jumpscale import j
import textwrap


class BuilderApache2(j.baseclasses.builder):

    __jslocation__ = "j.builders.web.apachectl"

    def build(self, reset=True):

        pkgs = "wget curl gcc libssl-dev zlib1g-dev libaprutil1-dev libapr1-dev libpcre3-dev libxml2-dev build-essential unzip".split()
        j.builders.system.package.ensure(pkgs)

        httpdir = "/optvar/build/httpd"

        if reset and j.builders.tools.dir_exists(httpdir):
            j.builders.tools.dir_remove("{DIR_BASE}/apps/apache2")

        j.core.tools.dir_ensure("/optvar/build")

        # DOWNLOAD LINK
        DOWNLOADLINK = "www-eu.apache.org/dist//httpd/httpd-2.4.29.tar.bz2"
        dest = j.sal.fs.joinPaths("/optvar", "httpd-2.4.29.tar.bz2")

        if not j.builders.tools.file_exists(dest):
            j.builders.tools.file_download(DOWNLOADLINK, dest)

        # EXTRACT SROURCE CODE
        j.sal.process.execute(
            "cd /optvar/build && tar xjf {dest} && cp -r /optvar/build/httpd-2.4.29 /optvar/build/httpd".format(
                **locals()
            )
        )
        j.core.tools.dir_ensure("{DIR_BASE}/apps/apache2/bin")
        j.core.tools.dir_ensure("{DIR_BASE}/apps/apache2/lib")

        buildscript = """

        cd {httpdir} &&  ./configure --prefix={DIR_BASE}/apps/apache2 --bindir={DIR_BASE}/apps/apache2/bin --sbindir={DIR_BASE}/apps/apache2/bin \
              --libdir={DIR_BASE}/apps/apache2/lib \
              --enable-mpms-shared=all \
              --enable-modules=all \
              --enable-mods-shared=all \
              --enable-so \
              --enable-cache --enable-disk-cache --enable-mem-cache --enable-file-cache \
              --enable-ssl --with-ssl \
              --enable-deflate --enable-cgi --enable-cgid \
              --enable-proxy --enable-proxy-connect \
              --enable-proxy-http --enable-proxy-ftp \
              --enable-dbd --enable-imagemap --enable-ident --enable-cern-meta \
              --enable-xml2enc && make && make test\
        """
        buildscript = self.replace(buildscript, args={"httpdir": httpdir})

        j.sal.process.execute(buildscript)

        return True

    def install(self):
        httpdir = j.sal.fs.joinPaths("/optvar/build", "httpd")
        installscript = """cd {httpdir} &&  make install""".format(httpdir=httpdir)
        j.sal.process.execute(installscript)

        # COPY APACHE BINARIES to /opt/jumpscale/bin
        j.builders.tools.file_copy("{DIR_BASE}/apps/apache2/bin/*", "{DIR_BIN}/")

    def configure(self):
        conffile = j.core.tools.file_text_read("{DIR_BASE}/apps/apache2/conf/httpd.conf")
        # SANE CONFIGURATIONS
        lines = """
        #LoadModule negotiation_module
        #LoadModule include_module
        #LoadModule userdir_module
        #LoadModule slotmem_shm_module
        #LoadModule rewrite_module modules/mod_rewrite.so
        #LoadModule mpm_prefork_module modules/mod_mpm_prefork.so

        #Include conf/extra/httpd-multilang-errordoc.con
        #Include conf/extra/httpd-autoindex.con
        #Include conf/extra/httpd-languages.con
        #Include conf/extra/httpd-userdir.con
        #Include conf/extra/httpd-default.con
        #Include conf/extra/httpd-mpm.con
        """.splitlines()

        for line in lines:
            line = line.strip()
            if line:
                mod = line.replace("#", "")
                conffile = conffile.replace(line, mod)
        disabled = """
        LoadModule mpm_worker_module modules/mod_mpm_worker.so
        LoadModule mpm_event_module modules/mod_mpm_event.so
        """
        for line in disabled.splitlines():
            line = line.strip()
            if line:
                mod = "#" + line
                conffile = conffile.replace(line, mod)
        sitesdirconf = j.builders.tools.replace("\nInclude %s/apache2/sites-enabled/*" % j.dirs.CFGDIR)
        conffile += sitesdirconf
        conffile += "\nAddType application/x-httpd-php .php"

        # MAKE VHOSTS DIRECTORY
        j.core.tools.dir_ensure("%s/apache2/sites-enabled/" % j.dirs.CFGDIR)
        j.core.tools.dir_ensure("{DIR_BASE}/apps/apache2/sites-available")
        j.core.tools.dir_ensure("{DIR_BASE}/apps/apache2/sites-enabled")
        # self._log_info("Config to be written = ", conffile)
        j.sal.fs.writeFile("{DIR_BASE}/apps/apache2/conf/httpd.conf", conffile)

    def start(self):
        """start Apache."""
        j.sal.process.execute("apachectl start", profile=True)

    def stop(self):
        """stop Apache."""
        j.sal.process.execute("apachectl stop", profile=True)

    def restart(self):
        """restart Apache."""
        j.sal.process.execute("apachectl restart", profile=True)
