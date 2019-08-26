from Jumpscale import j
import textwrap

builder_method = j.baseclasses.builder_method


class BuilderThreebot(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.threebot"

    def _init(self, **kwargs):
        self.BUILD_LOCATION = self._replace("{DIR_BUILD}/threebot")
        url = "https://github.com/threefoldtech/jumpscaleX_threebot/tree/%s/sandbox" % j.core.myenv.DEFAULTBRANCH
        self._sandbox_source = j.clients.git.getContentPathFromURLorPath(url)

    @builder_method()
    def install(self, reset=False):
        j.builders.web.openresty.install(reset=reset)
        j.builders.runtimes.lua.install(reset=reset)
        j.builders.db.zdb.install(reset=reset)
        j.builders.apps.sonic.install(reset=reset)
        self.base_bin()

    def base_bin(self, reset=False):
        """
        kosmos 'j.builders.apps.threebot.base_bin()'
        copy the files from the sandbox on jumpscale
        :param reset:
        :return:
        """
        self._copy(self._sandbox_source, "/sandbox")
        # DO NOT CHANGE ANYTHING HERE BEFORE YOU REALLY KNOW WHAT YOU'RE DOING

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None, flist_create=True):
        j.builders.runtimes.lua.sandbox(reset=reset)
        j.builders.db.zdb.sandbox(reset=reset)
        j.builders.apps.sonic.sandbox(reset=reset)

        self.tools.copyTree(j.builders.web.openresty.DIR_SANDBOX, self.DIR_SANDBOX)
        self.tools.copyTree(j.builders.runtimes.lua.DIR_SANDBOX, self.DIR_SANDBOX)
        self.tools.copyTree(j.builders.db.zdb.DIR_SANDBOX, self.DIR_SANDBOX)
        self.tools.copyTree(j.builders.apps.sonic.DIR_SANDBOX, self.DIR_SANDBOX)

        # sandbox openresty
        bins = ["openresty", "lua", "resty", "restydoc", "restydoc-index"]
        dirs = {
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/openresty.cfg"): "sandbox/cfg/nginx",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/mime.types"): "sandbox/cfg/nginx",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "openresty/"): "sandbox/openresty/",
            "/lib/x86_64-linux-gnu/libnss_files.so.2": "sandbox/lib/",
        }
        new_dirs = ["sandbox/var/pid/", "sandbox/var/log/"]
        root_files = {
            "etc/passwd": "nobody:x:65534:65534:nobody:/:/sandbox/bin/openresty",
            "etc/group": "nogroup:x:65534:",
        }
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

        for file_dest, content in root_files.items():
            file_dest = self.tools.joinpaths(self.DIR_SANDBOX, self.tools.path_relative(file_dest))
            dir = j.sal.fs.getDirName(file_dest)
            self.tools.dir_ensure(dir)
            self.tools.file_ensure(file_dest)
            self.tools.file_write(file_dest, content)

        self.tools.dir_ensure(self.DIR_SANDBOX + "etc/ssl/")
        self.tools.dir_ensure(self.DIR_SANDBOX + "etc/resty-auto-ssl")
        self.tools.copyTree("/sandbox/cfg/ssl/", self.DIR_SANDBOX + "etc/ssl/")
        self.tools.copyTree("/etc/resty-auto-ssl", self.DIR_SANDBOX + "etc/resty-auto-ssl")

        file = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates", "threebot_startup.toml")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, ".startup.toml")
        self._copy(file, file_dest)

        startup_file = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates", "3bot_startup.sh")
        file_dest = self.tools.joinpaths(self.DIR_SANDBOX, "3bot_startup.sh")
        self._copy(startup_file, file_dest)

    def start(self):
        j.servers.threebot.default.start()
        return True

    def stop(self):
        j.servers.threebot.default.stop()
        return True

    @builder_method()
    def test(self):
        assert self.start()
        assert self.stop()

        print("TEST OK")

    @builder_method()
    def clean(self):
        self._remove(self.BUILD_LOCATION)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()
