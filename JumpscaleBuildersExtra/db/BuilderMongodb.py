from Jumpscale import j
from time import sleep

builder_method = j.baseclasses.builder_method


class BuilderMongodb(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.mongod"

    def _init(self, **kwargs):
        self.DIR_DATA = self._replace("{DIR_VAR}/mongodb/data")
        self.DIR_HOME = self._replace("{DIR_VAR}/mongodb")
        self.BIN_PATH = self.tools.joinpaths(self.DIR_BUILD, "mongod")

    @builder_method()
    def clean(self):
        self._remove(self.DIR_BUILD)
        self._remove(self.DIR_HOME)
        self._remove(self.BIN_PATH)

    @builder_method()
    def install(self):
        """
        install, move files to appropriate places, and create relavent configs
        """
        # install: python3 buildscripts/scons.py --prefix=/opt/mongo install
        bin_path = self.tools.joinpaths(self.DIR_BUILD, "mongod")
        install_cmd = self._replace(
            """
            cp {BIN_PATH} {DIR_BIN}
            chown mongouser:mongouser {DIR_BIN}/mongod
            sudo -H -u mongouser mkdir {DIR_DATA}
        """
        )
        self._execute(install_cmd)

    @builder_method()
    def build(self):
        # needs libcurl-dev and libboost dependancies
        self.system.package.mdupdate()
        self.system.package.install(
            [
                "sudo",
                "libcurl4-openssl-dev",
                "build-essential",
                "libboost-filesystem-dev",
                "libboost-program-options-dev",
                "libboost-system-dev",
                "libboost-thread-dev",
                "gcc-8",
                "g++-8",
                "python3-pip",
                "libssl-dev",
                "libc6",
                "libc6-dev",
                "python3-dev",
            ]
        )
        # update gcc
        self._execute(
            """
            update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 800 --slave /usr/bin/g++ g++ /usr/bin/g++-8
            """
        )

        # create user

        self.tools.dir_ensure(self.DIR_HOME)
        cmd = self._replace(
            """
            id -u mongouser &>/dev/null || useradd mongouser --home {DIR_HOME} --no-create-home --shell /bin/bash
            chown -R mongouser:mongouser {DIR_HOME}
        """
        )
        self._execute(cmd)

        # build mongo

        mongo_url = "https://github.com/mongodb/mongo/"
        j.clients.git.pullGitRepo(url=mongo_url, dest=self.DIR_BUILD, branch="master", depth=1)

        build_cmd = """
        chown -R mongouser:mongouser {DIR_BUILD}

        cd {DIR_BUILD}
        sudo -H -u mongouser python3 -m pip install --user  -r etc/pip/compile-requirements.txt
        sudo -H -u mongouser buildscripts/scons.py mongod MONGO_VERSION=4.2.0
        """
        self._execute(self._replace(build_cmd), timeout=4000)

        self._execute(
            """
            update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 700 --slave /usr/bin/g++ g++ /usr/bin/g++-7
            """
        )

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @property
    def startup_cmds(self):
        cmd_start = self._replace(
            """
            chown -R mongouser:mongouser {DIR_HOME}
            sudo -H -u mongouser {DIR_BIN}/mongod --dbpath '{DIR_DATA}'
        """
        )

        cmd = j.servers.startupcmd.get(self._name, cmd_start=cmd_start)
        return [cmd]

    @builder_method()
    def stop(self):
        j.sal.process.killProcessByName(self._name)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()
        self.start()
        assert self.running()
        self.stop()
        print("TEST OK")

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

        sandbox_dir = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(sandbox_dir)

        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        bins = ["mongod"]
        for bin in bins:
            self._copy("{DIR_BIN}/" + bin, bin_dest)

        lib_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(bin_dest, bin)
            j.tools.sandboxer.libs_clone_under(dir_src, lib_dest)

        # startup.toml
        templates_dir = self.tools.joinpaths(j.sal.fs.getDirName(__file__), "templates")
        startup_path = self._replace("{DIR_SANDBOX}/.startup.toml")
        self._copy(self.tools.joinpaths(templates_dir, "mongodb_startup.toml"), startup_path)
