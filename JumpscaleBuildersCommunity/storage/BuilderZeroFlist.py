from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderZeroFlist(j.baseclasses.builder):
    __jslocation__ = "j.builders.storage.zflist"

    def _init(self, **kwargs):
        super()._init()
        self.datadir = ""

    def profile_builder_set(self):
        super().profile_builder_set()

    @builder_method()
    def build(self):
        """
        Builds zflist
        """
        cmd = """
        cd {DIR_BASE}/code/github/threefoldtech
        git clone -b development-v2 https://github.com/threefoldtech/0-flist.git

        cd 0-flist/autobuild/
        bash zflist.sh
        """
        j.sal.process.execute(cmd)

    @builder_method()
    def install(self):
        """
        Installs zflist
        """
        self.build()
        self._copy("/tmp/zflist", "{DIR_BIN}")

    @builder_method()
    def clean(self):
        """
        Remove built files
        """
        self._remove(self.DIR_SANDBOX)
        self._remove(j.core.tools.text_replace("{DIR_BASE}/code/github/threefoldtech/0-flist"))
        cmd = """
         rm -rf /opt/*
         """
        j.sal.process.execute(cmd)

    @builder_method()
    def sandbox(self):
        """
        Copy required bin files to be used to sandbox
        """
        # Copy zstor bins
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        bin_path = j.sal.fs.joinPaths(self._replace("{DIR_BIN}"), self._name)
        self._copy(bin_path, bin_dest)

    @builder_method()
    def uninstall(self):
        """
        Uninstall zflist by removing all related files from bin directory and build destination
        """
        bin_path = self.tools.joinpaths("{DIR_BIN}", self._name)
        self._remove(bin_path)
        self.clean()


