from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderTFChain(j.builders.system._BaseClass):
    NAME = "tfchain"

    @builder_method()
    def _init(self, reset=False):
        self.GIT_BRANCH = "master"
        self.DIR_BUILD = j.builders.runtimes.golang.package_path_get(
            self.__class__.NAME, host="github.com/threefoldfoundation"
        )

    @builder_method()
    def build(self, branch=None, tag=None, revision=None, reset=False):
        if self._done_get("build") and reset is False:
            return
        j.builders.system.package.mdupdate()
        j.builders.system.package.ensure("git")
        golang = j.builders.runtimes.golang
        golang.install()
        GOPATH = golang.GOPATH
        url = "github.com/threefoldfoundation"
        path = "%s/src/%s/tfchain" % (GOPATH, url)
        pullurl = "https://%s/tfchain.git" % url
        dest = j.clients.git.pullGitRepo(pullurl, branch=self.GIT_BRANCH, path=path)
        cmd = "cd {} && make install-std".format(dest)
        j.sal.process.execute(cmd)

    @builder_method()
    def install(self):
        self.build(branch=branch, tag=tag, revision=revision, reset=reset)
        tfchaindpath = j.builders.tools.joinpaths(j.builders.runtimes.golang.GOPATH, "bin", "tfchaind")
        tfchaincpath = j.builders.tools.joinpaths(j.builders.runtimes.golang.GOPATH, "bin", "tfchainc")
        j.builders.tools.file_copy(tfchaindpath, "{DIR_BIN}/")
        j.builders.tools.file_copy(tfchaincpath, "{DIR_BIN}/")

    def test(self):
        """
        kosmos 'j.builders.blockchain.tfchain.test()'
        :return:
        """
        self.install()
