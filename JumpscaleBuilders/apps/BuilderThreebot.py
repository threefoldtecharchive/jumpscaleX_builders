from Jumpscale import j
import textwrap

builder_method = j.baseclasses.builder_method


class BuilderThreebot(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.threebot"

    def _init(self, **kwargs):
        self.BUILD_LOCATION = self._replace("{DIR_BUILD}/threebot")
        url = "https://github.com/threefoldtech/jumpscaleX_core/tree/%s/sandbox" % j.core.myenv.DEFAULT_BRANCH
        self._sandbox_source = j.clients.git.getContentPathFromURLorPath(url)
        self.prebuilt_url = "https://github.com/threefoldtech/sandbox_threebot_linux64"
        self.path_cfg_dir = "{DIR_BASE}/cfg/nginx/default"
        self._web_path = "/{DIR_BASE}/var/web/default"

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
        self._copy(self._sandbox_source, "{DIR_BASE}")
        # DO NOT CHANGE ANYTHING HERE BEFORE YOU REALLY KNOW WHAT YOU'RE DOING

    @builder_method()
    def sandbox(self, reset=False, reset_deps=False, zhub_client=None, flist_create=False, push_to_repo=False):
        """

        kosmos 'j.builders.apps.threebot.sandbox(reset=True)'
        kosmos 'j.builders.apps.threebot.sandbox(reset=False)'

        :param reset:
        :param zhub_client:
        :param flist_create:
        :param push_to_repo:
        :return:
        """
        j.builders.db.zdb.sandbox(reset=reset_deps)

        j.builders.apps.sonic.sandbox(reset=reset_deps)
        j.builders.runtimes.python3.sandbox(reset=reset_deps)
        url = "https://github.com/threefoldtech/jumpscaleX_weblibs"
        weblibs_path = j.clients.git.getContentPathFromURLorPath(url, pull=False)

        # copy the templates to the right location
        self._copy(
            "{DIR_CODE}/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/openresty/web_resources",
            self.path_cfg_dir,
        )

        j.sal.fs.symlink("%s/static" % weblibs_path, "{}/static/weblibs".format(self._web_path), overwriteTarget=True)

        self._copy(j.builders.web.openresty.DIR_SANDBOX, self.DIR_SANDBOX)
        self._copy(j.builders.db.zdb.DIR_SANDBOX, self.DIR_SANDBOX)
        self._copy(j.builders.apps.sonic.DIR_SANDBOX, self.DIR_SANDBOX)
        self._copy(j.builders.runtimes.python3.DIR_SANDBOX, self.DIR_SANDBOX)

        script = """
        rsync -rav {DIR_CODE}/github/threefoldtech/jumpscaleX_core/sandbox/cfg/ {DIR_SANDBOX}/sandbox/cfg/
        rsync -rav {DIR_CODE}/github/threefoldtech/jumpscaleX_core/sandbox/bin/ {DIR_SANDBOX}/sandbox/bin/
        rsync -rav {DIR_CODE}/github/threefoldtech/jumpscaleX_core/sandbox/env.sh {DIR_SANDBOX}/sandbox/env.sh
        """
        self._execute(script)

        # sandbox openresty, THINK NO LONGER NEEDED, IS PART OF OPENRESTY FACTORY NOW
        bins = ["openresty", "lua", "resty", "restydoc", "restydoc-index"]
        dirs = {
            self._joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/openresty.cfg"): "sandbox/cfg/nginx",
            self._joinpaths(j.core.dirs.BASEDIR, "cfg/nginx/mime.types"): "sandbox/cfg/nginx",
            self._joinpaths(j.core.dirs.BASEDIR, "openresty/"): "sandbox/openresty/",
            "/lib/x86_64-linux-gnu/libnss_files.so.2": "sandbox/lib/",
        }
        new_dirs = ["sandbox/var/pid/", "sandbox/var/log/"]
        root_files = {
            "etc/passwd": "nobody:x:65534:65534:nobody:/:/sandbox/bin/openresty",
            "etc/group": "nogroup:x:65534:",
        }
        lua_files = j.sal.fs.listFilesInDir(self._joinpaths(j.core.dirs.BASEDIR, "bin/"), filter="*.lua")
        for file in lua_files:
            dirs[file] = "sandbox/bin/"

        for bin_name in bins:
            dir_src = self._joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self._joinpaths(self.DIR_SANDBOX, j.core.dirs.BINDIR[1:])
            self._dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox/lib")
        self._dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self._joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

        for dir_src, dir_dest in dirs.items():
            dir_dest = self._joinpaths(self.DIR_SANDBOX, dir_dest)
            self._dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        for dir_dest in new_dirs:
            dir_dest = self._joinpaths(self.DIR_SANDBOX, self.tools.path_relative(dir_dest))
            self._dir_ensure(dir_dest)
            self._touch(f"{dir_dest}/.keep")

        for file_dest, content in root_files.items():
            file_dest = self._joinpaths(self.DIR_SANDBOX, self.tools.path_relative(file_dest))
            dir = j.sal.fs.getDirName(file_dest)
            self._dir_ensure(dir)
            self.tools.file_ensure(file_dest)
            self.tools.file_write(file_dest, content)

        self._dir_ensure(self.DIR_SANDBOX + "/etc/ssl/")
        self._dir_ensure(self.DIR_SANDBOX + "/etc/resty-auto-ssl")
        self._dir_ensure(self.DIR_SANDBOX + "/bin")

        self._copy("{DIR_BASE}/cfg/ssl/", "{DIR_SANDBOX}/etc/ssl/")
        self._copy("/etc/resty-auto-ssl", "{DIR_SANDBOX}/etc/resty-auto-ssl")
        self._copy("{DIR_BASE}/bin", "{DIR_SANDBOX}/sandbox/bin", ignoredir=[".git"])
        self._copy("{DIR_BASE}/lib", "{DIR_SANDBOX}/sandbox/lib", ignoredir=[".git"])

        file = self._joinpaths(j.sal.fs.getDirName(__file__), "templates", "threebot_startup.toml")
        file_dest = self._joinpaths(self.DIR_SANDBOX, ".startup.toml")
        self._copy(file, file_dest)

        startup_file = self._joinpaths(j.sal.fs.getDirName(__file__), "templates", "3bot_startup.sh")
        file_dest = self._joinpaths(self.DIR_SANDBOX, "3bot_startup.sh")
        self._copy(startup_file, file_dest)

        js_dir = self.DIR_SANDBOX + j.core.tools.text_replace("{DIR_BASE}/lib/jumpscale")
        self._dir_ensure(js_dir)
        self._copy("{DIR_BASE}/lib/jumpscale/", js_dir, ignoredir=[".git"])

        if push_to_repo:
            repo_path = j.clients.git.pullGitRepo(self.prebuilt_url)
            self._copy(self.DIR_SANDBOX, repo_path)
            git_client = j.clients.git.get(repo_path)
            git_client.commit("update prebuilt file")
            git_client.push()

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
