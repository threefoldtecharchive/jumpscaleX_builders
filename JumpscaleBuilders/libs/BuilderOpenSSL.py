from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderOpenSSL(j.builders.system._BaseClass):

    NAME = "openssl"

    def __init__(self):
        if j.core.platformtype.myplatform.platform_is_osx:
            self.TARGET = "darwin64-x86_64-cc"
        else:
            self.TARGET = "linux-generic64"

        j.builders.system._BaseClass.__init__(self)

    @builder_method()
    def reset(self):
        self._remove("{DIR_BUILD}")

    @builder_method()
    def build(self, reset=False):
        """
        kosmos 'j.builders.libs.openssl.build(reset=True)'
        """
        self.tools.dir_ensure(self._replace("{DIR_BUILD}"))
        if not self.tools.exists(self.DIR_BUILD + "/openssl"):
            C = """
            set -ex
            cd {DIR_BUILD}
            git clone --depth 1 https://github.com/openssl/openssl.git
            """
            self._execute(C)

        C = """
        cd {DIR_BUILD}/openssl
        ./config -Wl,--enable-new-dtags,-rpath,'$(LIBRPATH)'
        ./Configure {TARGET} shared enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-comp --openssldir=/sandbox/var/openssl --prefix=/sandbox/ zlib
        make depend
        make install
        rm -rf /sandbox/share
        rm -rf /sandbox/build/private
        echo "**BUILD DONE**"
        """

        self._write("{DIR_BUILD}/mycompile_all.sh", C)
        self._execute("cd {DIR_BUILD}; sh ./mycompile_all.sh")

    def test(self, build=False):
        """
        kosmos 'j.builders.buildenv(build=True)'
        """
        if build:
            self.build()

        raise j.exceptions.Base("implement")

        print("TEST OK")
