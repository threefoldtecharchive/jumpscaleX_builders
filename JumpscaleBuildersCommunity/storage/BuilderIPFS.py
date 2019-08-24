from Jumpscale import j


class BuilderIPFS(j.builders.system._BaseClass):
    NAME = "ipfs"

    def isInstalled(self):
        """
        Checks if a package is installed or not
        You can ovveride it to use another way for checking
        """
        return j.builders.tools.file_exists("{DIR_BIN}/ipfs")

    def install(self, name="main", reset=False):
        if reset is False and self.isInstalled():
            return

        if j.builders.platformtype.platform_is_linux:
            url = "https://dist.ipfs.io/go-ipfs/v0.4.4/go-ipfs_v0.4.4_linux-amd64.tar.gz"
        elif "darwin" in j.builders.platformtype.osname:
            url = "https://dist.ipfs.io/go-ipfs/v0.4.4/go-ipfs_v0.4.4_darwin-amd64.tar.gz"

        name = url.split("/")[-1]
        compress_path = self._replace("{DIR_TEMP}/{}".format(name))
        j.builders.tools.file_download(url, compress_path)

        uncompress_path = self._replace("{DIR_TEMP}/go-ipfs")
        if j.builders.tools.file_exists(uncompress_path):
            j.builders.tools.dir_remove(uncompress_path)

        j.sal.process.execute("cd {DIR_TEMP}; tar xvf {}".format(name))
        j.builders.tools.file_copy("{}/ipfs".format(uncompress_path), "{DIR_BIN}/ipfs")

    def uninstall(self):
        """
        remove ipfs binary from {DIR_BIN}
        """
        if j.builders.tools.file_exists("{DIR_BIN}/ipfs"):
            j.builders.tools.file_unlink("{DIR_BIN}/ipfs")

    def start(self, name="main", readonly=False):
        cfg_dir = "{DIR_BASE}/cfg/ipfs/{}".format(name)
        if not j.builders.tools.file_exists(cfg_dir):
            j.core.tools.dir_ensure(cfg_dir)

        # check if the ipfs repo has not been created yet.
        if not j.builders.tools.file_exists(cfg_dir + "/config"):
            cmd = "IPFS_PATH={} {DIR_BIN}/ipfs init".format(cfg_dir)
            j.sal.process.execute(cmd)

        cmd = "{DIR_BIN}/ipfs daemon"
        if not readonly:
            cmd += "  --writable"

        pm = j.builders.system.processmanager.get()
        pm.ensure(name="ipfs_{}".format(name), cmd=cmd, path=cfg_dir, env={"IPFS_PATH": cfg_dir})

    def stop(self, name="main"):
        pm = j.builders.system.processmanager.get()
        pm.stop(name="ipfs_{}".format(name))
