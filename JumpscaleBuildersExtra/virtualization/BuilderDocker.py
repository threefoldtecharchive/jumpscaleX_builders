from Jumpscale import j
import random
import time

builder_method = j.baseclasses.builder_method


class BuilderDocker(j.baseclasses.builder):
    __jslocation__ = "j.builders.virtualization.docker"

    @builder_method()
    def build(self, branch=None):
        if j.core.platformtype.myplatform.platform_is_ubuntu:
            if not branch:
                if not self.tools.command_check("docker"):
                    C = """
                    wget -qO- https://get.docker.com/ | sh
                    """
                    self._execute(C)
                    j.builders.system.package.ensure("module-init-tools, aufs-tools")
                return
            j.builders.system.package.ensure(
                "apt-transport-https,linux-modules-extra-$(uname -r),linux-image-extra-virtual,software-properties-common"
            )
            _, release, _ = self._execute("echo $(lsb_release -cs)")
            if int(branch.split(".")[0]) > 1:
                self._execute("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -")
                self._execute(
                    "add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu %s stable'" % release
                )
                j.builders.system.package.mdupdate(reset=True)
                j.builders.system.package.ensure("libltdl7,aufs-tools")
                j.builders.system.package.ensure("docker-ce=%s.0~ce-0~ubuntu-xenial" % branch)
            else:
                self._execute(
                    "curl -fsSL 'https://sks-keyservers.net/pks/lookup?op=get&search=0xee6d536cf7dc86e2d7d56f59a178ac6c6238f52e' | apt-key add -"
                )
                self._execute(
                    "add-apt-repository 'deb https://packages.docker.com/%s/apt/repo/ ubuntu-%s main'"
                    % (branch, release)
                )
                j.builders.system.package.mdupdate(reset=True)
                j.builders.system.package.ensure("docker-engine")

        elif j.core.platformtype.myplatform.isArch:
            j.builders.system.package.ensure("docker")

    @builder_method()
    def install(self):
        j.builders.tools.file_copy("/usr/bin/docker", "{DIR_BIN}/docker")
        j.builders.tools.file_copy("/usr/bin/dockerd", "{DIR_BIN}/dockerd")
        j.builders.tools.file_copy("/usr/bin/dockerd-ce", "{DIR_BIN}/dockerd-ce")
        j.builders.tools.file_copy("/usr/bin/docker-proxy", "{DIR_BIN}/docker-proxy")
        j.builders.tools.file_copy("/usr/bin/docker-init", "{DIR_BIN}/docker-init")

    @property
    def startup_cmds(self):
        # docker daemon
        cmd = j.servers.startupcmd.get(self.NAME, cmd_start="dockerd")
        return [cmd]

    def stop(self):
        # killing the daemon
        j.sal.process.killProcessByName(self.NAME)

    @builder_method()
    def test(self):

        if self.running():
            self.stop()

        self.start()
        assert self.running()

        self._log_info("TEST SUCCESS: docker daemon is running")

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):

        dest_path = self.DIR_SANDBOX
        bins = ["docker", "dockerd", "dockerd-ce", "docker-init", "docker-proxy"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)
