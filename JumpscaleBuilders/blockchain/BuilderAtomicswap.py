from Jumpscale import j


class BuilderAtomicswap(j.baseclasses.builder):
    __jslocation__ = "j.builders.blockchain.atomicswap"

    def build(self, branch=None, tag=None, revision=None, reset=False):
        if self._done_get("build") and reset is False:
            return
        j.builders.system.package.mdupdate()
        j.builders.system.package.ensure("git")
        golang = j.builders.runtimes.golangtools
        golang.install()
        GOPATH = golang.GOPATH
        url = "github.com/rivine"
        path = "%s/src/%s/atomicswap" % (GOPATH, url)
        pullurl = "https://%s/atomicswap.git" % url
        dest = j.clients.git.pullGitRepo(pullurl, branch=branch, tag=tag, revision=revision, dest=path, ssh=False)
        cmd = "cd {} && make install".format(dest)
        j.sal.process.execute(cmd)

        self._done_set("build")

    def install(self, branch=None, tag="v0.1.0", revision=None, reset=False):
        # if branch, tag, revision = None it will build form master
        if self._done_get("install") and reset is False:
            return

        self.build(branch=branch, tag=tag, revision=revision, reset=reset)
        tfchaindpath = j.builders.tools.joinpaths(j.builders.runtimes.golangtools.GOPATH, "bin", "btcatomicswap")
        tfchaincpath = j.builders.tools.joinpaths(j.builders.runtimes.golangtools.GOPATH, "bin", "ethatomicswap")

        j.builders.tools.file_copy(tfchaindpath, "{DIR_BIN}/")
        j.builders.tools.file_copy(tfchaincpath, "{DIR_BIN}/")

        self._done_set("install")
