from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderGolang(BuilderGolangTools):

    __jslocation__ = "j.builders.runtimes.go"
    STABLE_VERSION = "1.12.1"
    DOWNLOAD_URL = "https://dl.google.com/go/go{version}.{platform}-{arch}.tar.gz"

    def _init(self, **kwargs):
        self.base_dir = self._replace("{DIR_BASE}")

        self.env = self.bash.profile
        self.DIR_GO_ROOT = self.tools.joinpaths(self.base_dir, "go")
        self.DIR_GO_PATH = self.tools.joinpaths(self.base_dir, "go_proj")
        self.DIR_GO_ROOT_BIN = self.tools.joinpaths(self.DIR_GO_ROOT, "bin")
        self.DIR_GO_PATH_BIN = self.tools.joinpaths(self.DIR_GO_PATH, "bin")

    @property
    def version(self):
        """get the current installed go version

        :raises j.exceptions.RuntimeError: in case go is not installed
        :return: go version e.g. 1.11.4
        :rtype: str
        """
        rc, out, err = self._execute("go version", die=False, showout=False)
        if rc:
            raise j.exceptions.RuntimeError("go is not instlled\n%s" % err)
        return j.data.regex.findOne(r"go\d+.\d+.\d+", out)[2:]

    @property
    def is_installed(self):
        """check if go is installed with the latest stable version

        :return: installed and the version is `VERSION_STABLE` or not
        :rtype: bool
        """
        try:
            version = self.version
            return self.STABLE_VERSION in version
        except j.exceptions.RuntimeError:
            return False

    @property
    def current_arch(self):
        """get the current arch string commonly used by go projects

        :return: arch (386 or amd64)
        :rtype: str
        """
        if j.core.platformtype.myplatform.is32bit:
            return "386"
        return "amd64"

    @builder_method()
    def install(self):
        """install goq

        kosmos 'j.builders.runtimes.go.install(reset=True)'

        """
        # only check for linux for now
        if j.core.platformtype.myplatform.platform_is_linux:
            download_url = self.DOWNLOAD_URL.format(
                version=self.STABLE_VERSION, platform="linux", arch=self.current_arch
            )
        elif j.core.platformtype.myplatform.platform_is_osx:
            download_url = self.DOWNLOAD_URL.format(
                version=self.STABLE_VERSION, platform="darwin", arch=self.current_arch
            )
        else:
            raise j.exceptions.RuntimeError("platform not supported")

        self._remove("{DIR_GO_PATH}")
        self._remove("{DIR_GO_ROOT}")

        j.core.tools.dir_ensure(self.DIR_GO_PATH)

        self.update_profile_paths()

        self.tools.file_download(
            download_url, self.DIR_GO_ROOT, overwrite=False, retry=3, timeout=0, expand=True, removeTopDir=True
        )

        self.get("github.com/tools/godep")
        self._done_set("install")

    def test(self):
        """test go installation

        to run:
        kosmos 'j.builders.runtimes.go.test()'
        """
        self.install()

        assert j.builders.runtimes.go.is_installed

        # test go get
        self.get("github.com/containous/go-bindata")
        package_path = self.package_path_get("containous/go-bindata")
        self._execute("cd %s && go install" % package_path)
