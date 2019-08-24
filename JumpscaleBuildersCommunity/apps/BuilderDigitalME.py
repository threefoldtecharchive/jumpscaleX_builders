from Jumpscale import j
import textwrap

builder_method = j.builders.system.builder_method


class BuilderDigitalME(j.baseclasses.builder):
    """
    specs:

        - build all required components (only work on ub 1804) using self.build
        - sandbox to sandbox dir
        - create flist
        - in self.test_zos() start the created flist & do the network tests for the openresty

    """

    __jslocation__ = "j.builders.apps.digitalme"

    @builder_method()
    def _init(self, **kwargs):
        pass

    @property
    def branch(self):
        _, current_digitalme_branch, _ = self._execute(
            "cd /sandbox/code/github/threefoldtech/digitalmeX/; git branch | grep \* | cut -d ' ' -f2"
        )
        return current_digitalme_branch.rstrip("\n")

    @builder_method()
    def build(self, reset=False):
        """
        kosmos 'j.tools.sandboxer.sandbox_build()'

        will build python & openresty & copy all to the right git sandboxes works for Ubuntu only
        :return:
        """
        j.builders.runtimes.python.build()
        j.builders.libs.openssl.build()
        j.builders.runtimes.lua.build()  # will build openresty & lua & openssl
        j.clients.git.pullGitRepo(url="https://github.com/threefoldtech/digitalmeX.git", branch=self.branch)

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None, flist_create=False):
        j.builders.runtimes.python.sandbox(reset=reset)
        j.builders.runtimes.lua.sandbox(reset=reset)
        j.tools.sandboxer.copyTo(j.builders.runtimes.python.DIR_SANDBOX, "{}/sandbox".format(self.DIR_SANDBOX))
        j.tools.sandboxer.copyTo(j.builders.runtimes.lua.DIR_SANDBOX, self.DIR_SANDBOX)
        git_repo_path = "/sandbox/code/github/threefoldtech/digitalmeX"
        j.tools.sandboxer.copyTo(git_repo_path, j.sal.fs.joinPaths(self.DIR_SANDBOX, git_repo_path[1:]))

    @property
    def startup_cmds(self):
        cmd = j.servers.startupcmd.get(
            "openresty", cmd_start="openresty", cmd_stop="openresty -s stop", path="/sandbox/bin"
        )
        return [cmd]

    def gslides(self):
        """
        kosmos 'j.builders.apps.digitalme.gslides()'
        google slides option
        :return:
        """
        j.shell()
        "google-api-python-client,google-auth-httplib2,google-auth-oauthlib"

    def test(self, zos_client=None):
        """
        j.builders.apps.digitalme.test()
        test locally, start openresty and do network check
        :return:
        """
        self.sandbox()
        self.start()
        assert j.sal.nettools.waitConnectionTest("localhost", 8081, timeoutTotal=10)
        self._log_info("TEST OK FOR DIGITAL ME BUILDING")

    def test_zos(self, zos_client, zhubclient):
        flist = self.sandbox(zhub_client=zhubclient)
        container_id = zos_client.container.create(flist, name="test_digitalme").get()
        container_client = zos_client.cotainer.client(container_id)
        assert container_client.ping()
        # TODO: find a way to check if openresty started on the container
