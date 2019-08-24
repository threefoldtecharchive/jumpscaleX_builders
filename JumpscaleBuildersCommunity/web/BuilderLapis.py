from Jumpscale import j
import os
import textwrap
from time import sleep


class BuilderLapis(j.baseclasses.builder):
    __jslocation__ = "j.builders.web.lapis"

    def _init(self, **kwargs):
        self.BUILDDIR = self._replace("{DIR_VAR}/build/")
        self.bins = [
            "/bin/mkdir",
            "/bin/touch",
            self.tools.joinpaths(j.core.dirs.BINDIR, "openresty"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "lua"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "resty"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "restydoc"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "restydoc-index"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "lapis"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "moon"),
            self.tools.joinpaths(j.core.dirs.BINDIR, "moonc"),
        ]
        self.dirs = {
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/openresty.cfg"): "cfg/",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "cfg/mime.types"): "cfg/",
            self.tools.joinpaths(j.core.dirs.BASEDIR, "openresty/"): "openresty/",
            "/lib/x86_64-linux-gnu/libnss_files.so.2": "lib",
        }
        lua_files = j.sal.fs.listFilesInDir(self.tools.joinpaths(j.core.dirs.BASEDIR, "bin/"), filter="*.lua")
        for file in lua_files:
            self.dirs[file] = "bin/"

        self.root_dirs = {
            "/usr/bin/perl": "usr/bin/",
            "/usr/bin/env": "usr/bin/",
            "/bin/sh": "bin/",
            "/usr/lib/x86_64-linux-gnu/perl-base/": "usr/lib/x86_64-linux-gnu/perl-base/",
        }

        self.new_dirs = ["var/pid/", "var/log/"]
        startup_file = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "templates", "lapis_startup.toml")
        self.startup = j.sal.fs.readFile(startup_file)
        self.root_files = {
            "etc/passwd": "nobody:x:65534:65534:nobody:/:/sandbox/bin/openresty",
            "etc/group": "nogroup:x:65534:",
        }

    def build(self, reset=False):
        j.builders.runtimes.lua.build(reset)

    def install(self, reset=False):
        j.builders.runtimes.lua.install(reset)
