from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderARDB(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.ardb"

    def _init(self, **kwargs):
        # forest db (backend engine) paths
        self.CODE_DIR_FDB = self._replace("{DIR_BUILD}/github/couchbase/forestdb")
        self.BUILD_DIR_FDB = self._replace("{DIR_BUILD}/forestdb/")
        # ardb build paths
        self.CODE_DIR_ARDB = self._replace("{DIR_BUILD}/github/yinqiwen/ardb")
        self.BUILD_DIR_ARDB = self._replace("{DIR_BUILD}/ardb/")

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.db.ardb.build()'
        """
        # build_forest_db
        self.build_forest_db()

        # Default packages needed
        packages = ["wget", "bzip2", "git", "libbz2-dev", "unzip"]

        # Install dependancies
        self.system.package.install(packages)

        url = "https://github.com/yinqiwen/ardb.git"
        j.clients.git.pullGitRepo(url=url, tag="v0.9.7", dest=self.CODE_DIR_ARDB, depth=1)

        storageEngine = "forestdb"
        C = """
            set -ex
            cd {CODE_DIR_ARDB}
            # cp {BUILD_DIR_ARDB}/FDB/libforestdb* .
            storage_engine=$storageEngine make
            rm -rf {BUILD_DIR_ARDB}/ARDB/
            mkdir -p {BUILD_DIR_ARDB}/ARDB
            cp src/ardb-server {BUILD_DIR_ARDB}/ARDB/
            cp ardb.conf {BUILD_DIR_ARDB}/ARDB/
            """.format(
            CODE_DIR_ARDB=self.CODE_DIR_ARDB, BUILD_DIR_ARDB=self.BUILD_DIR_ARDB
        )
        C = C.replace("$storageEngine", storageEngine)
        self._execute(self._replace(C))

    # build forest_db as backend
    def build_forest_db(self):

        j.builders.libs.cmake.install()
        self.system.package.mdupdate()
        self.system.package.install(["git-core", "libsnappy-dev", "g++", "libaio-dev"])

        url = "git@github.com:couchbase/forestdb.git"
        j.clients.git.pullGitRepo(url=url, dest=self.CODE_DIR_FDB, tag="v1.2", depth=1)

        C = """
            set -ex
            cd {CODE_DIR_FDB}
            mkdir build
            cd build
            cmake ../
            make all
            rm -rf {BUILD_DIR_FDB}/FDB/
            mkdir -p {BUILD_DIR_FDB}/FDB
            cp forestdb_dump* {BUILD_DIR_FDB}/FDB/
            cp forestdb_hexamine* {BUILD_DIR_FDB}/FDB/
            cp libforestdb* {BUILD_DIR_FDB}/FDB/
            """.format(
            CODE_DIR_FDB=self.CODE_DIR_FDB, BUILD_DIR_FDB=self.BUILD_DIR_FDB
        )
        self._execute(C)

    @builder_method()
    def install(self,):
        """
        as backend use ForestDB
        """
        self.tools.dir_ensure("{DIR_BIN}")
        self._copy("{BUILD_DIR_ARDB}/ARDB/ardb-server", "{DIR_BIN}/ardb-server")

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and reate flist if create_flist = True

        :param reset: reset sandbox file transfer
        :type reset: bool
        :type flist_create:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        self._copy("{DIR_BIN}/ardb-server", bin_dest)

        lib_dest = self.tools.joinpaths(self.DIR_SANDBOX, "lib", "x86_64-linux-gnu")
        self.tools.dir_ensure(lib_dest)
        dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, "ardb-server")
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest)

    @builder_method()
    def test(self):
        """
        do some test through normal redis client
        """
        j.builders.db.ardb.start()
        r = j.clients.redis.get(ipaddr="0.0.0.0", port=16379)
        r.set("test", "test")
        assert r.get("test") == b"test"
        r.delete("test")
        j.builders.db.ardb.stop()
        print("TEST OK")

    @property
    def startup_cmds(self):
        cmds = j.servers.startupcmd.get(name=self._name, cmd_start=self._name)
        return [cmds]

    @builder_method()
    def stop(self):
        j.sal.process.killProcessByName(self._name)

    @builder_method()
    def clean(self):
        self._remove(self.CODE_DIR_FDB)
        self._remove(self.BUILD_DIR_FDB)
        self._remove(self.CODE_DIR_ARDB)
        self._remove(self.BUILD_DIR_ARDB)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()
