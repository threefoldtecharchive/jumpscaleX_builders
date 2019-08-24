from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderBrotli(j.builders.system._BaseClass):
    NAME = "brotli"

    def _init(self, **kwargs):
        self.src_dir = self.DIR_BUILD + "/code/"

    @builder_method()
    def build(self):

        # install cmake
        j.builders.libs.cmake.install()

        # build from source code
        src_url = "https://github.com/google/brotli.git"
        j.clients.git.pullGitRepo(src_url, dest=self.src_dir, branch="master", depth=1, ssh=False)
        build_cmd = """
        cd {}
        mkdir out && cd out
        cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=./installed ..
        cmake --build . --config Release --target install
        """.format(
            self.src_dir
        )
        self._execute(build_cmd)

    @builder_method()
    def install(self):
        # install bins
        build_src = j.sal.fs.joinPaths(self.src_dir, "out", "installed")
        bin_src = j.sal.fs.joinPaths(build_src, "bin")
        lib_src = j.sal.fs.joinPaths(build_src, "lib")
        include_src = j.sal.fs.joinPaths(build_src, "include")

        self._copy(bin_src + "/brotli", "/sandbox/bin/")

        # install libs
        libs = [
            "libbrotlicommon.so",
            "libbrotlidec.so",
            "libbrotlienc.so",
            "libbrotlicommon.so.1",
            "libbrotlidec.so.1",
            "libbrotlienc.so.1",
            "libbrotlicommon.so.1.0.7",
            "libbrotlienc.so.1.0.7",
            "libbrotlidec.so.1.0.7",
        ]
        for lib in libs:
            self._copy(lib_src + "/" + lib, "/sandbox/lib/")

        # copy includes
        self._copy(include_src, "/sandbox/include/")

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=True, merge_base_flist=""):
        bin_src = "/sandbox/bin/brotli"
        lib_src = "/sandbox/lib/"
        include_src = "/sandbox/include/brotli"

        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        lib_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "lib")
        include_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "include", "brotli")

        self.tools.dir_ensure(bin_dest)
        self.tools.dir_ensure(lib_dest)
        self.tools.dir_ensure(include_dest)

        self._copy(bin_src, bin_dest)

        # install libs
        libs = [
            "libbrotlicommon.so",
            "libbrotlidec.so",
            "libbrotlienc.so",
            "libbrotlicommon.so.1",
            "libbrotlidec.so.1",
            "libbrotlienc.so.1",
            "libbrotlicommon.so.1.0.7",
            "libbrotlienc.so.1.0.7",
            "libbrotlidec.so.1.0.7",
        ]
        for lib in libs:
            self._copy(lib_src + lib, lib_dest)

        # copy includes
        self._copy(include_src, include_dest)

    @builder_method()
    def clean(self):
        C = """
        set -ex
        rm -rf {}
        """.format(
            self.DIR_BUILD
        )
        self._execute(C)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def test(self):
        cmd_create = """
        cd /tmp/
        echo test a file > mybrotli
        md5sum mybrotli
        """
        _, md5_src, _ = self._execute(cmd_create)

        cmd_compressed = """
        cd /tmp/
        brotli mybrotli
        brotli -d mybrotli.br -o debrotli
        md5sum debrotli
        """
        _, md5_out, _ = self._execute(cmd_compressed)

        cmd_clean = """
        cd /tmp/
        rm mybrotli debrotli mybrotli.br
        """
        self._execute(cmd_clean)
        assert md5_src.split()[0] == md5_out.split()[0]

        print("TEST OK")
