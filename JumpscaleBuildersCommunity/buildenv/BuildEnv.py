from Jumpscale import j


class BuildEnv(j.builders.system._BaseFactoryClass):

    __jslocation__ = "j.builders.buildenv"

    def install(self, reset=False, upgrade=True):

        if self._done_check("install", reset):
            return

        self.upgrade()

        if not self._done_check("fixlocale", reset):
            j.tools.bash.get().profile.locale_check()
            self._done_set("fixlocale")

        # out = ""
        # make sure all dirs exist
        # for key, item in j.builders.tools.dir_paths.items():
        #     out += "mkdir -p %s\n" % item
        # j.sal.process.execute(out)

        j.builders.system.package.mdupdate()

        # if not j.core.platformtype.myplatform.platform_is_osx and not j.builders.tools.isCygwin:
        #     j.builders.system.package.ensure("fuse")

        if j.builders.tools.isArch:
            # is for wireless auto start capability
            j.builders.system.package.ensure("wpa_actiond,redis-server")

        if j.core.platformtype.myplatform.platform_is_osx:
            C = ""
        else:
            C = "sudo net-tools python3 python3-distutils python3-psutil"

        C += " openssl wget curl git mc tmux rsync"
        j.builders.system.package.ensure(C)

        # j.builders.sandbox.profileJS.path_add("{DIR_BIN}")
        # j.builders.sandbox.profileJS.save()

        if upgrade:
            self.upgrade(reset=reset, update=False)

        self._done_set("install")

    def development(self, reset=False, python=False):
        """
        install all components required for building (compiling)

        to use e.g.
            kosmos 'j.builders.buildenv.development()'

        """

        C = """
        autoconf
        gcc
        make
        autoconf
        libtool
        pkg-config
        curl
        """
        C = j.core.text.strip(C)

        if j.core.platformtype.myplatform.platform_is_osx:

            if not self._done_get("xcode_install"):
                j.sal.process.execute("xcode-select --install", die=False, showout=True)
                cmd = "sudo installer -pkg /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg -target /"
                j.sal.process.execute(cmd, die=False, showout=True)
                self._done_set("xcode_install")

            C += "libffi "
            C += "automake "
            C += "pcre "
            C += "xz "
            C += "openssl "
            C += "zlib "
        else:
            C += "libffi-dev "
            C += "build-essential "
            C += "libsqlite3-dev "
            C += "libpq-dev "
            if python:
                C += "python3-dev "

        self.install()
        if self._done_check("development", reset):
            return
        j.builders.system.package.ensure(C)
        self._done_set("development")

    def upgrade(self, reset=False, update=True):
        if self._done_check("upgrade", reset):
            return
        if update:
            j.builders.system.package.mdupdate(reset=reset)
        j.builders.system.package.upgrade(reset=reset)
        j.builders.system.package.clean()

        self._done_set("upgrade")
