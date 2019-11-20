from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderLibffi(j.baseclasses.builder):
    __jslocation__ = "j.builders.libs.libffi"

    def _init(self, **kwargs):
        self.LIBFFI_URL = "https://github.com/libffi/libffi"
        self.INSTALL_DIR = self.DIR_SANDBOX + "/sandbox"
        self._dir_ensure(self.INSTALL_DIR)
        self.CODEDIR = self._replace("{DIR_TEMP}/libffi")

    @builder_method()
    def build(self):
        self.system.package.ensure("autoconf")
        self.system.package.ensure("libtool")
        j.clients.git.pullGitRepo(url=self.LIBFFI_URL, dest=self.CODEDIR, depth=1)
        cmd = """
        cd {}
        set -ex
        ./autogen.sh
        ./configure  --prefix={} --disable-docs
        make
        make install
        """.format(
            self.CODEDIR, self.INSTALL_DIR
        )
        self._execute(cmd)

    @builder_method()
    def install(self):
        self._copy(self.INSTALL_DIR, "/sandbox")

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        pass
