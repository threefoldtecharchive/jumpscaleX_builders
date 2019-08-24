from Jumpscale import j
from Jumpscale.builders.runtimes.BuilderGolang import BuilderGolangTools

import os
import textwrap

builder_method = j.builders.system.builder_method


class BuilderMinio(BuilderGolangTools):
    NAME = "minio"

    def _init(self, **kwargs):
        super()._init()
        self.datadir = ""

    def profile_builder_set(self):
        super().profile_builder_set()
        self.profile.env_set("GO111MODULE", "on")

    @builder_method()
    def build(self):
        """
        Builds minio
        """
        # install gnutls dependancy
        self.system.package.mdupdate()
        self.system.package.install("gnutls-bin")

        j.builders.runtimes.golang.install()
        self.get("github.com/minio/minio")

    @builder_method()
    def install(self):
        """
        Installs minio
        """
        self._copy("{}/bin/minio".format(self.DIR_GO_PATH), "{DIR_BIN}")

    @property
    def startup_cmds(self):
        """
        Starts minio.
        """
        self.datadir = self.DIR_BUILD
        address = "0.0.0.0"
        self.tools.dir_ensure(self.datadir)
        port = 9000
        access_key = "admin"
        secret_key = "adminadmin"
        cmd = "MINIO_ACCESS_KEY={} MINIO_SECRET_KEY={} minio server --address {}:{} {}".format(
            access_key, secret_key, address, port, self.datadir
        )
        cmds = [j.servers.startupcmd.get(name=self.NAME, cmd_start=cmd)]
        return cmds

    @builder_method()
    def clean(self):
        self._remove(self.DIR_SANDBOX)
        self._remove("{}/bin/minio".format(j.builders.runtimes.golang.DIR_GO_PATH))

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and reate flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type flist_create:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        dest_path = self.DIR_SANDBOX
        dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, "minio")
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(bin_dest)
        dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
        self.tools.dir_ensure(dir_dest)
        self._copy(dir_src, dir_dest)
        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        pid = j.sal.process.getProcessPid(self.NAME)
        assert pid is not []
        self.stop()

        print("TEST OK")

    @builder_method()
    def uninstall(self):
        bin_path = self.tools.joinpaths("{DIR_BIN}", self.NAME)
        self._remove(bin_path)
        self.clean()
