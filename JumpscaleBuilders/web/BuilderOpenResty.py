from Jumpscale import j
import os
import textwrap
from time import sleep

builder_method = j.baseclasses.builder_method


class BuilderOpenResty(j.baseclasses.builder):
    __jslocation__ = "j.builders.web.openresty"

    @builder_method()
    def build(self, reset=False):
        """
        kosmos 'j.builders.web.openresty.build()'
        :return:
        """

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            j.builders.system.package.mdupdate()
            j.builders.system.package.ensure("build-essential libpcre3-dev libssl-dev zlib1g-dev")

        url = "https://openresty.org/download/openresty-1.13.6.2.tar.gz"

        dest = self._replace("{DIR_BUILD}/openresty")
        self.tools.file_download(
            url, to=dest, overwrite=False, retry=3, expand=True, minsizekb=1000, removeTopDir=True, deletedest=True
        )
        C = """
        cd {DIR_BUILD}/openresty
        mkdir -p {DIR_BASE}/var/pid
        mkdir -p {DIR_BASE}/var/log
        ./configure \
            --with-cc-opt="-I/usr/local/opt/openssl/include/ -I/usr/local/opt/pcre/include/" \
            --with-ld-opt="-L/usr/local/opt/openssl/lib/ -L/usr/local/opt/pcre/lib/" \
            --prefix="{DIR_BASE}/openresty" \
            --sbin-path="{DIR_BASE}/bin/openresty" \
            --modules-path="{DIR_BASE}/lib" \
            --pid-path="{DIR_BASE}/var/pid/openresty.pid" \
            --error-log-path="{DIR_BASE}/var/log/openresty.log" \
            --lock-path="{DIR_BASE}/var/nginx.lock" \
            --conf-path="{DIR_BASE}/cfg/nginx/openresty.cfg" \
            -j8
        make -j8
        make install
        """
        self._execute(C)

    @builder_method()
    def install(self, **kwargs):
        """
        kosmos 'j.builders.web.openresty.install()'
        #will call the build step
        :param kwargs:
        :return:
        """
        # copy the files from the sandbox !!! IMPORTANT

        C = """
        ln -sf {DIR_BASE}/openresty/bin/resty {DIR_BASE}/bin/resty
        ln -sf {DIR_BASE}/openresty/bin/restydoc {DIR_BASE}/bin/restydoc
        ln -sf {DIR_BASE}/openresty/bin/restydoc-index {DIR_BASE}/bin/restydoc-index
        ln -f -s {DIR_BASE}/openresty/luajit/bin/luajit {DIR_BASE}/bin/lua
        rm  -rf {DIR_BASE}/openresty/pod
        rm  -rf {DIR_BASE}/openresty/site
        """
        self._execute(C)

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """

        kosmos 'j.builders.web.openresty.sandbox()'

        Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """

        bins = ["openresty", "lua", "resty", "restydoc", "restydoc-index"]
        dirs = {
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/openresty.cfg"): "sandbox/cfg/nginx",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/mime.types"): "sandbox/cfg/nginx",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "openresty/"): "sandbox/openresty/",
            "/lib/x86_64-linux-gnu/libnss_files.so.2": "sandbox/lib/",
        }
        new_dirs = ["sandbox/var/pid/", "sandbox/var/log/"]
        lua_files = j.sal.fs.listFilesInDir(self.tools.joinpaths(j.core.dirs.BASEDIR, "bin/"), filter="*.lua")
        for file in lua_files:
            dirs[file] = "sandbox/bin/"

        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(self.DIR_SANDBOX, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self.tools.joinpaths(self.DIR_SANDBOX, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

        for dir_src, dir_dest in dirs.items():
            dir_dest = self.tools.joinpaths(self.DIR_SANDBOX, dir_dest)
            self.tools.dir_ensure(dir_dest)
            self.tools.copyTree(dir_src, dir_dest)

        for dir_dest in new_dirs:
            dir_dest = self.tools.joinpaths(self.DIR_SANDBOX, self.tools.path_relative(dir_dest))
            self.tools.dir_ensure(dir_dest)

        cur_dir = j.sal.fs.getDirName(__file__)
        startup_file = self.tools.joinpaths(cur_dir, "templates", "openresty_startup.toml")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, ".startup.toml")
        self._copy(startup_file, file_dest)

    @builder_method()
    def clean(self, reset=False):
        """
        kosmos 'j.builders.web.openresty.clean()'
        :return:
        """
        C = """
        cd {DIR_BASE}
        rm -rf {DIR_BUILD}
        rm -f {DIR_BASE}/bin/lua*
        rm -f {DIR_BASE}/bin/moon*
        rm -f {DIR_BASE}/bin/openresty*
        rm -f {DIR_BASE}/bin/resty*
        rm -f {DIR_BASE}/bin/_moon*
        rm -f {DIR_BASE}/bin/_lapis*
        rm -f {DIR_BASE}/bin/lapis*
        rm -rf {DIR_BASE}/openresty/

        """
        self._execute(C)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    def copy_to_github(self, reset=False):
        """
        js_shell 'j.builders.web.openresty.copy_to_github(reset=True)'
        js_shell 'j.builders.web.openresty.copy_to_github()'
        :return:
        """
        raise j.exceptions.Base("check despiegk: not immplemented yet")
        self.build(reset=reset)

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            CODE_SB_BIN = j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_ubuntu.git")
        elif j.core.platformtype.myplatform.platform_is_osx:
            CODE_SB_BIN = j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_osx.git")
        else:
            raise j.exceptions.Base("only ubuntu & osx support")

        CODE_SB_BASE = j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_base.git")

        C = """
        set -ex

        cp {SRCBINDIR}/resty* {CODE_SB_BASE}/base/bin/
        rm -f {CODE_SB_BIN}/base/bin/resty*

        cp {SRCBINDIR}/openresty {CODE_SB_BASE}/base/bin/
        rm -f {CODE_SB_BIN}/base/bin/openresty

        cp {DIR_BIN}/*.lua {CODE_SB_BASE}/base/bin/
        rm -f {CODE_SB_BIN}/base/bin/*.lua

        cp {DIR_BIN}/lapis {CODE_SB_BASE}/base/bin/
        rm -f {CODE_SB_BIN}/base/bin/lapis

        cp {DIR_BIN}/lua {CODE_SB_BIN}/base/bin/
        rm -f {CODE_SB_BASE}/base/bin/lua

        cp {DIR_BIN}/moon* {CODE_SB_BASE}/base/bin/
        rm -f {CODE_SB_BIN}/base/bin/moon*

        cp {DIR_BIN}/openresty {CODE_SB_BIN}/base/bin/
        rm -f {CODE_SB_BASE}/base/bin/openresty

        """
        args = {}
        args["CODE_SB_BIN"] = CODE_SB_BIN
        args["CODE_SB_BASE"] = CODE_SB_BASE
        args["SRCBINDIR"] = j.core.tools.text_replace("{DIR_BASE}/openresty/bin")
        args["BINDIR"] = j.core.tools.text_replace("{DIR_BASE}/bin")

        self.tools.execute(C, args=args)

    @property
    def startup_cmds(self):
        cmd = """
        rm -rf {DIR_TEMP}/lapis_test
        mkdir -p {DIR_TEMP}/lapis_test 
        cd {DIR_TEMP}/lapis_test
        lapis --lua new
        lapis server
        """
        cmd = self._replace(cmd)
        cmds = [j.servers.startupcmd.get("test_openresty", cmd_start=cmd, ports=[8080], process_strings_regex="^nginx")]
        return cmds

    def test(self):
        """
        kosmos 'j.builders.web.openresty.test()'

        server is running on port 8080

        """
        j.builders.web.openresty.install()
        j.builders.runtimes.lua.install()

        if self.running():
            self.stop()
        self.start()
        self._log_info("openresty is running on port 8080")
        # we now have done a tcp test, lets do a http client connection
        out = j.clients.http.get("http://localhost:8080")
        assert out.find("Welcome to Lapis 1.7.0") != -1  # means message is there
        self.stop()

        self._log_info("openresty test was ok,no longer running")
