from Jumpscale import j
from random import randint

builder_method = j.baseclasses.builder_method


class BuilderRedis(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.redis"

    @builder_method()
    def build(self):
        if j.core.platformtype.myplatform.platform_is_ubuntu:
            j.builders.system.package.mdupdate()
            j.builders.system.package.ensure("build-essential")

            j.builders.tools.dir_remove("{DIR_TEMP}/build/redis")

            C = """
            #!/bin/bash
            set -ex
            mkdir -p {DIR_TEMP}/build/redis
            cd {DIR_TEMP}/build/redis
            wget http://download.redis.io/redis-stable.tar.gz
            tar xzf redis-stable.tar.gz
            cd redis-stable
            make

            """
            self._execute(C)

        else:
            raise j.exceptions.NotImplemented(message="only ubuntu supported for building redis")

    @builder_method()
    def install(self):
        """
         will build if required & then install binary on right location
        :return:
        """
        self.build()
        self._copy("{DIR_TEMP}/build/redis/redis-stable/src/redis-server", "{DIR_BIN}", overwrite=False)
        self._copy("{DIR_TEMP}/build/redis/redis-stable/src/redis-cli", "{DIR_BIN}", overwrite=False)
        j.builders.tools.dir_remove("{DIR_BASE}/apps/redis")

    @property
    def startup_cmds(self):
        cmds = [
            j.servers.startupcmd.get(
                name="redis_server", cmd_start="redis-server --port {}".format(randint(6000, 7000))
            )
        ]
        return cmds

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """
        dest_path = self.DIR_SANDBOX

        bins = ["redis-server", "redis-cli"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)
