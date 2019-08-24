from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderNodeJS(j.baseclasses.builder):
    __jslocation__ = "j.builders.runtimes.nodejs"

    def _init(self, **kwargs):
        self._version = "6.9.5"

    @property
    def npm(self):
        return self._replace("{DIR_BASE}/%s/bin/npm" % self.NAME)

    @property
    def NODE_PATH(self):
        return self._replace("{DIR_BASE}/%s/lib/node_modules" % self.NAME)

    @property
    def path(self):
        return self._replace("{DIR_BASE}/%s" % self.NAME)

    def phantomjs(self, reset=False):
        """
        headless browser used for automation
        """
        if j.core.platformtype.myplatform.platform_is_ubuntu:

            url = "https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2"
            cdest = j.builders.tools.file_download(
                url, expand=True, overwrite=False, to="{DIR_TEMP}/phantomjs", removeTopDir=True, deletedest=True
            )

            j.builders.tools.execute("mv %s/bin/phantomjs /opt/bin/phantomjs" % cdest)
            j.builders.tools.execute("rm -rf %s" % cdest)

            j.builders.system.package.ensure("libfontconfig")

        elif j.core.platformtype.myplatform.platform_is_osx:
            j.builders.system.package.ensure("phantomjs")

        else:
            raise j.exceptions.Base("phantomjs only supported don ubuntu or osx")

    def npm_install(self, name, global_=True):
        """
        @PARAM cmdname is the optional cmd name which will be used to put in path of the env (as alias to the name)
        """
        self._log_info("npm install:%s" % name)
        key = "npm_%s" % name
        if global_:
            if j.core.platformtype.myplatform.platform_is_osx:
                sudo = "sudo "
            else:
                sudo = ""
            cmd = "cd /tmp;%snpm install -g %s --unsafe-perm=true --allow-root" % (sudo, name)
        else:
            cmd = "cd %s;npm i %s" % (self.NODE_PATH, name)

        j.sal.process.execute(cmd)

    @builder_method()
    def build(self):
        j.builders.tools.dir_remove(self.DIR_BUILD)
        if j.core.platformtype.myplatform.platform_is_osx:
            url = "https://nodejs.org/dist/v%s/node-v%s-darwin-x64.tar.gz" % (self._version, self._version)
        elif j.core.platformtype.myplatform.platform_is_ubuntu:
            url = "https://nodejs.org/dist/v%s/node-v%s-linux-x64.tar.gz" % (self._version, self._version)
        else:
            raise j.exceptions.Input(message="only support ubuntu & mac")

        j.builders.tools.file_download(
            url, expand=True, overwrite=False, to=self.DIR_BUILD, removeTopDir=True, keepsymlinks=True
        )

    @builder_method()
    def install(self, reset=False):

        j.builders.tools.execute("rm -rf %s;cp -r %s %s" % (self.path, self.DIR_BUILD, self.path))
        j.builders.tools.file_link("%s/bin/node" % self.path, "{DIR_BIN}/node")
        j.builders.tools.file_link("%s/bin/npm" % self.path, "{DIR_BIN}/npm")

        rc, out, err = j.sal.process.execute("npm -v")
        if out.replace("\n", "") != "3.10.10":
            raise j.exceptions.Base("npm version error")

        rc, initmodulepath, err = j.sal.process.execute("npm config get init-module")
        j.builders.tools.file_unlink(initmodulepath)
        j.sal.process.execute("npm config set global true -g")
        j.sal.process.execute(self._replace("npm config set init-module %s/.npm-init.js -g" % self.path))
        j.sal.process.execute(self._replace("npm config set init-cache %s/.npm -g" % self.path))
        j.sal.process.execute("npm config set global true ")
        j.sal.process.execute(self._replace("npm config set init-module %s/.npm-init.js" % self.path))
        j.sal.process.execute(self._replace("npm config set init-cache %s/.npm" % self.path))
        j.sal.process.execute("npm install -g parcel-bundler")

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        self.tools.dir_ensure(self.DIR_SANDBOX)
        self._copy(self.path, "%s/%s/%s" % (self.DIR_SANDBOX, j.core.dirs.BASEDIR[1:], self.NAME))

        bin_dest = self.tools.joinpaths(self.DIR_SANDBOX, j.core.dirs.BINDIR[1:])
        self.tools.dir_ensure(bin_dest)

        self._copy(self.tools.joinpaths(j.core.dirs.BINDIR, "node"), bin_dest)
        self._copy(self.tools.joinpaths(j.core.dirs.BINDIR, "npm"), bin_dest)

    @builder_method()
    def test(self):
        rc, out, err = j.sal.process.execute("npm -v")
        assert out.replace("\n", "") == "3.10.10"
