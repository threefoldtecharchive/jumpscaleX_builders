from Jumpscale import j
from Jumpscale.tools.bash.Profile import Profile

builder_method = j.baseclasses.builder_method


class BuilderLua(j.baseclasses.builder):
    """
    needs openresty and openssl
    """

    __jslocation__ = "j.builders.runtimes.lua"

    def _init(self, **kwargs):
        self.ROCKS_PATHS_PROFILE = self._replace("{DIR_BUILD}/rocks_paths")

    @builder_method()
    def build(self, reset=False, deps_reset=False):
        """
        kosmos 'j.builders.runtimes.lua.build(reset=True)'
        :param install:
        :return:
        """
        if j.core.platformtype.myplatform.platform_is_ubuntu:
            j.builders.system.package.install(
                ["libsqlite3-dev", "libpcre3-dev", "libssl-dev", "perl", "make", "build-essential"]
            )

        j.builders.web.openresty.install(reset=deps_reset)
        # j.builders.libs.openssl.build(reset=deps_reset)  #DOES NOT WORK FOR NOW, maybe wrong version of openssl?

        url = "https://luarocks.org/releases/luarocks-3.1.3.tar.gz"
        dest = self._replace("{DIR_BUILD}/luarocks")
        self.tools.dir_ensure(dest)
        self.tools.file_download(
            url, to=dest, overwrite=False, retry=3, expand=True, minsizekb=100, removeTopDir=True, deletedest=True
        )
        C = """
        cd {DIR_BUILD}/luarocks
        ./configure --prefix={DIR_BASE}/openresty/luarocks --with-lua={DIR_BASE}/openresty/luajit
        make build
        make install

        cp {DIR_BUILD}/luarocks/luarocks {DIR_BASE}/bin/luarocks
        luarocks path > {ROCKS_PATHS_PROFILE}
        """

        # set showout to False to avoid text_replace of output log
        self._execute(C, showout=True)

    def profile_luarocks_select(self):
        self.profile_builder_select()

        def _clean_env(env_paths):
            build_lua_path = self._replace("{DIR_BUILD}/luarocks/")
            clean_path = ";".join(
                [
                    path
                    for path in env_paths.split(";")
                    if not (path.startswith(build_lua_path) or path.startswith(j.core.myenv.config["DIR_HOME"]))
                ]
            )
            return clean_path

        if not j.sal.fs.exists(self.ROCKS_PATHS_PROFILE):
            self.build(reset=True)
            assert j.sal.fs.exists(self.ROCKS_PATHS_PROFILE)

        if not j.sal.fs.exists(j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/include")):
            # we need the include headers so if not there need to build openresty
            j.builders.web.openresty.build(reset=True)

        # add lua_path and lua_cpath so lua libs/clibs can found by lua interpreter)
        luarocks_profile = Profile(self._bash, self.ROCKS_PATHS_PROFILE)

        lua_path = luarocks_profile.env_get("LUA_PATH")
        lua_path = _clean_env(lua_path)

        lua_cpath = luarocks_profile.env_get("LUA_CPATH")
        lua_cpath = _clean_env(lua_cpath)

        # ADD items from sandbox
        LUALIB = j.core.tools.text_replace("{DIR_BASE}/openresty/lualib")
        assert j.sal.fs.exists(LUALIB)
        self.profile.env_set("LUALIB", LUALIB)

        lua_path = (
            "?.lua;$LUALIB/?/init.lua;$LUALIB/?.lua;$LUALIB/?/?.lua;$LUALIB/?/core.lua;{DIR_BASE}/openresty/lapis/?.lua;"
            + lua_path.strip('"')
        )
        lua_path = lua_path.replace("$LUALIB", LUALIB)

        self.profile.env_set("LUA_PATH", lua_path, quote=True)

        lua_cpath = "$LUALIB/?.so" + lua_cpath.strip('"')
        lua_cpath = lua_cpath.replace("$LUALIB", LUALIB)

        self.profile.env_set("LUA_CPATH", lua_cpath, quote=True)

        LUAINCDIR = j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/include/luajit-2.1")
        assert j.sal.fs.exists(LUAINCDIR)
        self.profile.env_set("LUA_INCDIR", LUAINCDIR)
        self.profile.path_add(j.core.tools.text_replace("{DIR_BASE}/bin"))

        path = luarocks_profile.env_get("PATH")  # .replace(";", ":")
        self.profile.path_add(path, check_exists=False)

    def lua_rock_install(self, name, reset=False, profileset=True):
        """
        kosmos 'j.builders.runtimes.lua.lua_rock_install("lua-resty-auto-ssl")'
        :param name:
        :param reset:
        :return:
        """
        self._log_info("lua_rock_install: %s" % name)
        if profileset:
            self.profile_luarocks_select()

        if not reset and self._done_check("lua_rock_install_%s" % name):
            return

        if j.core.platformtype.myplatform.platform_is_osx:
            C = "luarocks install $NAME CRYPTO_DIR=$CRYPTODIR OPENSSL_DIR=$CRYPTODIR "
            CRYPTODIR = "/usr/local/opt/openssl"
            assert j.sal.fs.exists(CRYPTODIR)
            C = C.replace("$CRYPTODIR", CRYPTODIR)
        else:
            # C = "luarocks install $NAME CRYPTO_DIR=$CRYPTODIR OPENSSL_DIR=$CRYPTODIR"
            # C = "luarocks install lapis CRYPTO_DIR={DIR_BASE} OPENSSL_DIR={DIR_BASE}"
            C = "luarocks install $NAME "
            C = C.replace("$CRYPTODIR", j.core.tools.text_replace("{DIR_BASE}"))
        C = C.replace("$NAME", name)
        # example crypto dir: /usr/local/openresty/openssl/

        self._execute(C)

        self._done_set("lua_rock_install_%s" % name)

    @builder_method()
    def lua_rocks_install(self, reset=True):
        """
        kosmos 'j.builders.runtimes.lua.install()'
        #will call this
        :param install:
        :return:
        """
        self.profile_luarocks_select()

        C = """
        luaossl
        lua-resty-auto-ssl
        # luasec
        lapis
        moonscript
        lapis-console
        LuaFileSystem
        # luasocket
        lua-cjson
        # lua-term
        # penlight
        # lpeg
        # mediator_lua

        # inspect

        lua-resty-redis-connector
        # lua-resty-openidc

        # LuaRestyRedis

        # lua-capnproto
        lua-toml

        # lua-resty-exec

        # lua-resty-influx
        lua-resty-repl
        #
        # lua-resty-iputils
        #
        # lsqlite3
        #
        # bcrypt
        # md5

        # date
        # uuid
        # lua-resty-cookie
        # lua-path

        # luazen

        # alt-getopt
        lua-messagepack

        # lua-resty-qless
        # lua-geoip
        # luajwt
        # mooncrafts

        """

        for line in C.split("\n"):
            line = line.strip()
            if line == "":
                continue
            if line.startswith("#"):
                continue
            self.lua_rock_install(line, reset=reset, profileset=False)

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            self.lua_rock_install("lua-geoip", reset=reset)
            self.lua_rock_install("lua-resty-jwt", reset=reset)
            self.lua_rock_install("lua-resty-iyo-auth", reset=reset)  # need to check how to get this to work on OSX

        cmd = "rsync -rav  {DIR_BASE}/openresty/luarocks/lua_modules/lib/lua/5.1/ {DIR_BASE}/openresty/lualib"
        self.tools.execute(cmd, die=False)
        cmd = "rsync -rav {DIR_BASE}/openresty/luarocks/share/lua/5.1/  {DIR_BASE}/openresty/lualib/"
        self.tools.execute(cmd, die=False)
        cmd = "rsync -rav {DIR_BASE}/openresty/luarocks/lib/lua/5.1/  {DIR_BASE}/openresty/lualib/"
        self.tools.execute(cmd, die=False)

    # def build_crypto(self):
    #
    #     """
    #     # https://github.com/evanlabs/luacrypto
    #
    #     export OPENSSL_CFLAGS=-I/usr/local/opt/openssl/include/
    #     export OPENSSL_LIBS="-L/usr/local/opt/openssl/lib -lssl -lcrypto"
    #     export LUAJIT_LIB=j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/lib")
    #     export LUAJIT_INC=j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/include/luajit-2.1")
    #     export LUA_CFLAGS="-I{DIR_BASE}/openresty/luajit/include/luajit-2.1/"
    #     export LUA_LIB=j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/lib")
    #     export LUA_INC=j.core.tools.text_replace("{DIR_BASE}/openresty/luajit/include/luajit-2.1")
    #
    #     :return:
    #     """

    @builder_method()
    def clean(self):
        """
        kosmos 'j.builders.runtimes.lua.cleanup()'
        :param install:
        :return:
        """

        C = """

        set -ex

        rm -rf {DIR_BASE}/openresty/luarocks
        rm -rf /bin/resty-auto-ssl
        rm -rf {DIR_BUILD}
        rm -rf /tmp/luarocks*
        """
        self._execute(C)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def install(self, reset=False, deps_reset=False):
        """
        will build & install in sandbox
        kosmos 'j.builders.runtimes.lua.install(reset=False)'
        :return:
        """
        j.builders.web.openresty.install(reset=deps_reset)
        self.lua_rocks_install(reset=deps_reset)

        # will get the sandbox files, important that these files get there unmodified
        j.builders.apps.threebot.base_bin()

        # copy some binaries
        C = """

        set -e
        pushd {DIR_BASE}/openresty/luarocks/lib/luarocks/rocks-5.1/lapis/1.7.0-1/bin/
        cp lapis {DIR_BASE}/bin/_lapis.lua
        cp lapis {DIR_BASE}/bin/lapis
        popd
        pushd j.core.tools.text_replace("{DIR_BASE}/openresty/luarocks/lib/luarocks/rocks-5.1/moonscript/0.5.0-1/bin")
        cp moon {DIR_BASE}/bin/_moon.lua
        cp moonc {DIR_BASE}/bin/_moonc.lua
        popd


        """
        self._execute(C)

        self.install_autossl()

        self.install_certificates()

    def install_autossl(self):
        """
        kosmos 'j.builders.runtimes.lua.install_autossl()'
        :return:
        """
        if self.tools.platform_is_ubuntu:
            C = """
            ln -sf {DIR_BASE}/openresty/luarocks/bin/resty-auto-ssl/ {DIR_BASE}/openresty/resty-auto-ssl
            ln -sf {DIR_BASE}/openresty/luarocks/bin/resty-auto-ssl/ /bin/resty-auto-ssl
            mkdir -p /etc/resty-auto-ssl/storage/file
            """
            self._execute(C)
        else:
            C = """
            ln -sf {DIR_BASE}/openresty/luarocks/bin/resty-auto-ssl {DIR_BASE}/openresty/resty-auto-ssl
            """

            self._execute(C)

        ssl_path = j.core.tools.text_replace("{DIR_BASE}/cfg/ssl")
        j.sal.fs.createDir(ssl_path)
        if self.tools.platform_is_ubuntu:
            j.sal.unix.addSystemGroup("www")
            j.sal.unix.addSystemUser("www", "www")
            j.sal.fs.chown(ssl_path, "www", "www")
            j.sal.fs.chmod(ssl_path, 0o755)
            j.sal.fs.chown("/etc/resty-auto-ssl", "www", "www")
            j.sal.fs.chmod("/etc/resty-auto-ssl", 0o755)
            j.sal.fs.chown("/bin/resty-auto-ssl", "www", "www")
            j.sal.fs.chmod("/bin/resty-auto-ssl", 0o755)

        self.install_certificates()

    @builder_method()
    def install_certificates(self, reset=False):
        """
        kosmos 'j.builders.runtimes.lua.install_certificates()'
        :return:
        """
        assert self._exists(j.core.tools.text_replace("{DIR_BASE}/openresty/resty-auto-ssl"))
        ssl_path = j.core.tools.text_replace("{DIR_BASE}/cfg/ssl")
        j.sal.fs.createDir(ssl_path)
        # Generate a self signed fallback certificate
        cmd = """
        openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 \
            -subj '/CN=sni-support-required-for-valid-ssl' \
            -keyout %s/resty-auto-ssl-fallback.key \
            -out %s/resty-auto-ssl-fallback.crt
        """ % (
            ssl_path,
            ssl_path,
        )
        self._execute(cmd)

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None):
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """
        dest_path = self.DIR_SANDBOX
        j.builders.web.openresty.sandbox()

        bins = ["lua", "lapis", "moon", "moonc"]
        # bins = ["lua", "_lapis.lua", "_moonc.lua", "_moon.lua", "_moonrocks.lua", "lapis", "moon", "moonc"]
        # TODO: this was the original, we prob need to copy more
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    def copy_to_github(self):
        """
        kosmos 'j.builders.runtimes.lua.copy_to_github()'
        :return:
        """
        # assert self.executor.type=="local"
        path = j.core.tools.text_replace("{DIR_BASE}/openresty/lualib")

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            destbin = "%s/base/openresty/lualib" % j.clients.git.getContentPathFromURLorPath(
                "git@github.com:threefoldtech/sandbox_ubuntu.git"
            )
        elif j.core.platformtype.myplatform.platform_is_osx:
            destbin = "%s/base/openresty/lualib" % j.clients.git.getContentPathFromURLorPath(
                "git@github.com:threefoldtech/sandbox_osx.git"
            )
        else:
            raise j.exceptions.Base("only ubuntu & osx support")

        dest = "%s/base/openresty/lualib" % j.clients.git.getContentPathFromURLorPath(
            "git@github.com:threefoldtech/sandbox_base.git"
        )

        for item in j.sal.fs.listFilesInDir(path, recursive=True):
            rdest = j.sal.fs.pathRemoveDirPart(item, path)
            if j.sal.fs.getFileExtension(item) == "so":
                d2 = destbin
            elif j.sal.fs.getFileExtension(item) == "lua":
                d2 = dest
            else:
                raise j.exceptions.Base(item)
            dir_dest_full = j.sal.fs.getDirName(self.tools.joinpaths(d2, rdest))
            self.tools.dir_ensure(dir_dest_full)
            dest_full = self.tools.joinpaths(d2, rdest)
            self._copy(item, dest_full)

        self.clean()

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
        kosmos 'j.builders.runtimes.lua.test()'

        server is running on port 8080

        """

        if self.running():
            self.stop()
        self.start()
        self._log_info("openresty is running on port 8080")
        # we now have done a tcp test, lets do a http client connection
        out = j.clients.http.get("http://localhost:8080")

        assert out.find("Welcome to Lapis 1.7.0") != -1  # means message is there
        self.stop()

        self._log_info("openresty test was ok,no longer running")


