from Jumpscale import j


builder_method = j.baseclasses.builder_method


class BuilderNIM(j.baseclasses.builder):
    __jslocation__ = "j.builders.runtimes.nim"

    def _init(self, **kwargs):

        self.DIR_BUILD = self._replace("{DIR_VAR}/build/nimlang")

    @builder_method()
    def build(self):

        """
        kosmos 'j.builders.runtimes.nim.build()'
        :return:
        """
        self.profile_sandbox_select()
        download_url = "https://nim-lang.org/download/nim-0.19.4.tar.xz"

        self.tools.file_download(download_url, overwrite=False, to=self.DIR_BUILD, expand=True, removeTopDir=True)

        C = """
        cd {DIR_BUILD}
        sh build.sh
        bin/nim c koch
        ./koch tools
        """

        self._execute(C)

    @builder_method()
    def install(self):

        self.build()
        nim_bin_path = self.tools.joinpaths(self.DIR_BUILD, "bin")

        j.builders.tools.dir_ensure(nim_bin_path)
        self._copy("%s/nim" % nim_bin_path, "{DIR_BIN}/nim")

    @builder_method()
    def sandbox(self):
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(bin_dest)
        self._copy("{DIR_BUILD}/bin/", bin_dest)

    @builder_method()
    def test(self):
        self.install()

        rc, _, _ = self._execute("nim --v | grep Version")
        if rc:
            print("TEST Failed")
            return
        print("TEST DONE")
