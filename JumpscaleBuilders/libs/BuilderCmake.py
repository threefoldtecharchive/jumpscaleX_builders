from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderCmake(j.baseclasses.builder):
    __jslocation__ = "j.builders.libs.cmake"

    def _init(self, **kwargs):
        self.package_path = self._replace("{DIR_TEMP}/CMake")

    @builder_method()
    def build(self):
        cmake_url = "https://github.com/Kitware/CMake"
        j.clients.git.pullGitRepo(url=cmake_url, dest=self.package_path, depth=1)
        cmd = """
        cd {}
        ./bootstrap --prefix=/sandbox && make
        """.format(
            self.package_path
        )
        self._execute(cmd, timeout=15 * 60)

    @property
    def share_src(self):
        dir_list = j.sal.fs.listDirsInDir(j.core.tools.text_replace("{DIR_BASE}/share"))
        return [i for i in dir_list if i.startswith(j.core.tools.text_replace("{DIR_BASE}/share/cmake"))][0]

    @builder_method()
    def install(self):
        self._execute("cd {} && make install".format(self.package_path))
        self.profile.env_set_part("LD_LIBRARY_PATH", j.core.tools.text_replace("{DIR_BASE}/lib/"))

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        # bins
        bins = ["cmake", "cpack", "ctest"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(self.DIR_SANDBOX, j.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        # libs
        lib_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

        # share
        share_dest = self.tools.joinpaths(self.DIR_SANDBOX, self.share_src[1:])
        self.tools.dir_ensure(share_dest)
        self._copy(self.share_src, share_dest)

    def clean(self):
        self._remove(self.package_path)
        self._remove(self.share_src)

    def test(self):
        path = self._execute("which cmake", showout=False)
        assert path[1].strip() == j.core.tools.text_replace("{DIR_BASE}/bin/cmake")
        print("TEST OK")

