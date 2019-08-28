from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderGolangTools(j.baseclasses.builder):
    __jslocation__ = "j.builders.runtimes.golangtools"

    def _init(self, **kwargs):
        self.base_dir = self._replace("{DIR_BASE}")

        self.env = self.bash.profile
        self.DIR_GO_ROOT = self.tools.joinpaths(self.base_dir, "go")
        self.DIR_GO_PATH = self.tools.joinpaths(self.base_dir, "go_proj")
        self.DIR_GO_ROOT_BIN = self.tools.joinpaths(self.DIR_GO_ROOT, "bin")
        self.DIR_GO_PATH_BIN = self.tools.joinpaths(self.DIR_GO_PATH, "bin")

    def update_profile_paths(self, profile=None):
        if not profile:
            profile = self.bash.profile

        profile.env_set("GOROOT", self.DIR_GO_ROOT)
        profile.env_set("GOPATH", self.DIR_GO_PATH)

        # remove old parts of profile
        # and add them to PATH (without existence check)
        profile.path_delete("/go/")
        profile.path_delete("/go_proj")
        profile.path_add(self.DIR_GO_PATH_BIN, check_exists=False)
        profile.path_add(self.DIR_GO_ROOT_BIN, check_exists=False)

    def profile_builder_set(self):
        # make sure go binaries are in path while building
        self.update_profile_paths(self.profile)

    @builder_method()
    def goraml(self):
        """install (using go get) goraml.

        :param reset: reset installation, defaults to False
        :type reset: bool, optional
        """
        self.bindata()

        C = """
        go get -u github.com/tools/godep
        go get -u github.com/jteeuwen/go-bindata/...
        go get -u github.com/Jumpscale/go-raml
        set -ex
        cd {DIR_GO_PATH}/src/github.com/Jumpscale/go-raml
        sh build.sh
        """
        self._execute(C)
        self._done_set("goraml")

    @builder_method()
    def bindata(self):
        """install (using go get) go-bindata.

        :param reset: reset installation, defaults to False
        :type reset: bool, optional
        """

        C = """
        set -ex
        go get -u github.com/jteeuwen/go-bindata/...
        cd {DIR_GO_PATH}/src/github.com/jteeuwen/go-bindata/go-bindata
        go build
        go install
        """
        self._execute(C)

    @builder_method()
    def glide(self):
        """install glide"""
        self.tools.file_download("https://glide.sh/get", "{DIR_TEMP}/installglide.sh", minsizekb=4)
        self._execute(". {DIR_TEMP}/installglide.sh")
        self._done_set("glide")

    def get(self, url, install=True, update=False, die=True, verbose=False):
        """go get a package

        :param url: pacakge url e.g. github.com/tools/godep
        :type url:  str
        :param install: build and install the repo if false will only get the repo, defaults to True
        :type install: bool, optional
        :param update: will update requirements if they exist, defaults to True
        :type update: bool, optional
        :param die: raise a RuntimeError if failed, defaults to True
        :type die: bool, optional
        """
        flags = ""
        if not install:
            flags = " -d"
        if update:
            flags += " -u"
        if verbose:
            flags += " -v"
        self._execute("go get %s %s" % (flags, url), timeout=10000, die=die)

    def package_path_get(self, name, host="github.com", go_path=None):
        """A helper method to get a package path installed by `get`
        Will use this builder's default go path if go_path is not provided

        :param name: pacakge name e.g. containous/go-bindata
        :type name: str
        :param host: host, defaults to github.com
        :type host: str
        :param go_path: GOPATH, defaults to None
        :type go_path: str

        :return: go package path
        :rtype: str
        """
        if not go_path:
            go_path = self.DIR_GO_PATH
        return self.tools.joinpaths(go_path, "src", host, name)

    def godep(self, url, branch=None, depth=1):
        """install a package using godep

        :param url: package url e.g. github.com/tools/godep
        :type url: str
        :param branch: a specific branch, defaults to None
        :type branch: str, optional
        :param depth: depth to pull with, defaults to 1
        :type depth: int, optional
        """
        pullurl = "git@%s.git" % url.replace("/", ":", 1)

        dest = j.clients.git.pullGitRepo(
            pullurl, branch=branch, depth=depth, dest="%s/src/%s" % (self.DIR_GO_PATH, url), ssh=False
        )
        self._execute("cd %s && godep restore" % dest)