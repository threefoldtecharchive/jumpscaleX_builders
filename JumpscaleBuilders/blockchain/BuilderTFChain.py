from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderTFChain(BuilderGolangTools):
    __jslocation__ = "j.builders.blockchain.tfchain"

    @builder_method()
    def _init(self, reset=False):
        self.GIT_BRANCH = "master"
        self.DIR_BUILD = self.package_path_get(self.__class__.NAME, host="github.com/threefoldfoundation")

    @builder_method()
    def build(self, branch=None, tag=None, revision=None, reset=False):
        if self._done_get("build") and reset is False:
            return
        j.builders.system.package.mdupdate()
        j.builders.system.package.ensure("git")
        golang = j.builders.runtimes.go
        golang.install()
        GOPATH = golang.DIR_GO_PATH
        url = "github.com/threefoldfoundation"
        path = "%s/src/%s/tfchain" % (GOPATH, url)
        pullurl = "https://%s/tfchain.git" % url
        dest = j.clients.git.pullGitRepo(pullurl, branch=self.GIT_BRANCH, path=path)
        cmd = "cd {} && make install-std".format(dest)
        j.sal.process.execute(cmd)

    @builder_method()
    def install(self):
        self.build(branch=branch, tag=tag, revision=revision, reset=reset)
        tfchaindpath = j.builders.tools.joinpaths(self.DIR_GO_PATH, "bin", "tfchaind")
        tfchaincpath = j.builders.tools.joinpaths(self.DIR_GO_PATH, "bin", "tfchainc")
        j.builders.tools.file_copy(tfchaindpath, "{DIR_BIN}/")
        j.builders.tools.file_copy(tfchaincpath, "{DIR_BIN}/")

    def test(self):
        """
        kosmos 'j.builders.blockchain.tfchain.test()'
        :return:
        """
        self.install()
