from Jumpscale import j

JSBASE = j.baseclasses.builder

builder_method = j.builders.system.builder_method


class BuilderCapnp(JSBASE):
    __jslocation__ = "j.builders.libs.capnp"

    @builder_method()
    def build(self):
        """
        install capnp

        kosmos 'j.builders.libs.capnp.build(reset=True)'
        kosmos 'j.builders.libs.capnp.build()'
        """

        # j.builders.buildenv.install()
        if self.tools.platform_is_ubuntu:
            j.builders.system.package.ensure("g++")

        # build tools
        self.system.package.mdupdate()
        self.system.package.install(["autoconf", "automake", "libtool"])

        # build from source
        install_cmd = """
        cd {DIR_BUILD}
        rm -rf capnproto
        git clone --depth 1 https://github.com/sandstorm-io/capnproto.git
        cd capnproto/c++
        autoreconf -i
        ./configure
        make -j6 check
        make install
        """
        self._execute(install_cmd, timeout=1000)

    @builder_method()
    def install(self):
        """
        install capnp

        kosmos 'j.builders.libs.capnp.install()'
        """
        if self.tools.platform_is_ubuntu:
            j.builders.system.package.ensure("g++")
        # j.builders.runtimes.python.pip_package_install(['cython', 'setuptools', 'pycapnp'])
        bins = ["capnp", "capnp-afl-testcase", "capnpc-c++", "capnp-test", "capnpc-capnp", "capnp-evolution-test"]

        libs = [
            "libkj-http.so",
            "libkj-async.so",
            "libcapnpc.so",
            "libkj-tls.so",
            "libcapnp.so",
            "libkj-test.so",
            "libcapnp-json.so",
            "libcapnp-rpc.so",
            "libkj.so",
            "libkj-async-0.8-dev.so",
            "libkj-test-0.8-dev.so",
            "libcapnpc-0.8-dev.so",
            "libcapnp-json-0.8-dev.so",
            "libcapnp-0.8-dev.so",
            "libkj-0.8-dev.so",
            "libkj-http-0.8-dev.so",
            "libkj-tls-0.8-dev.so",
            "libcapnp-rpc-0.8-dev.so",
        ]
        # copy bins
        bins_src_path = "{DIR_BUILD}/capnproto/c++/.libs/"
        for bin in bins:
            self._copy(bins_src_path + bin, "{DIR_BIN}")

        # copy libs
        for lib in libs:
            self._copy(bins_src_path + lib, "/sandbox/lib")

    @builder_method()
    def clean(self):
        code_dir = j.sal.fs.joinPaths(self.DIR_BUILD, "capnproto")
        self._remove(code_dir)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=True, merge_base_flist=""):
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        lib_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "lib")

        bins = ["capnp", "capnp-afl-testcase", "capnpc-c++", "capnp-test", "capnpc-capnp", "capnp-evolution-test"]

        libs = [
            "libkj-http.so",
            "libkj-async.so",
            "libcapnpc.so",
            "libkj-tls.so",
            "libcapnp.so",
            "libkj-test.so",
            "libcapnp-json.so",
            "libcapnp-rpc.so",
            "libkj.so",
            "libkj-async-0.8-dev.so",
            "libkj-test-0.8-dev.so",
            "libcapnpc-0.8-dev.so",
            "libcapnp-json-0.8-dev.so",
            "libcapnp-0.8-dev.so",
            "libkj-0.8-dev.so",
            "libkj-http-0.8-dev.so",
            "libkj-tls-0.8-dev.so",
            "libcapnp-rpc-0.8-dev.so",
        ]
        # copy bins
        for bin in bins:
            self.tools.dir_ensure(bin_dest)
            bin_src = j.sal.fs.joinPaths("/sandbox/bin/", bin)
            self._copy(bin_src, bin_dest)

        # copy libs
        for lib in libs:
            self.tools.dir_ensure(lib_dest)
            lib_src = j.sal.fs.joinPaths("/sandbox/lib/", lib)
            self._copy(lib_src, lib_dest)

    @builder_method()
    def test(self):
        """
        kosmos 'j.builders.builder.libs.capnp.test()'
        """
        return_code, _, _ = self._execute("capnp-test")
        assert return_code == 0
        print("TEST OK")
