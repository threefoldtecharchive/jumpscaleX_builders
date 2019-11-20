from Jumpscale import j
import json

builder_method = j.baseclasses.builder_method
JSBASE = j.baseclasses.builder


class BuilderZerotier(j.baseclasses.builder):
    __jslocation__ = "j.builders.network.zerotier"

    def _init(self, **kwargs):
        self.DIR_BUILD = "{DIR_VAR}/build/zerotier/"
        self.CLI = j.core.tools.text_replace("{DIR_BASE}/bin/zerotier-cli")

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def clean(self):
        j.sal.fs.remove(self.DIR_BUILD)
        j.sal.fs.remove(self.DIR_SANDBOX)

    @builder_method()
    def build(self, reset=False):
        """
        kosmos 'j.builders.network.zerotier.build()'
        :return: 
        """

        if j.core.platformtype.myplatform.platform_is_osx:
            raise j.exceptions.Base("not supported yet")

            # j.sal.process.execute("xcode-select --install", die=False, showout=True)
        # elif j.core.platformtype.myplatform.platform_is_ubuntu:

        j.builders.system.package.ensure("gcc")
        j.builders.system.package.ensure("g++")
        j.builders.system.package.ensure("make")

        self.DIR_CODEL = j.clients.git.pullGitRepo(
            "https://github.com/zerotier/ZeroTierOne", reset=reset, depth=1, branch="master"
        )

        S = """
            cd {DIR_CODEL}
            export DESTDIR={DIR_BUILD}
            make one
            make install        
            """
        self._execute(S)

        # cmd = "cd {code} &&  make one".format(code=codedir, build=self.DIR_BUILD)
        # j.sal.process.execute(cmd)
        # if j.core.platformtype.myplatform.platform_is_osx:
        #     cmd = "cd {code} && make install-mac-tap".format(code=codedir, build=self.DIR_BUILD)
        #     bindir = '{DIR_BIN}'
        #     j.core.tools.dir_ensure(bindir)
        #     for item in ['zerotier-cli', 'zerotier-idtool', 'zerotier-one']:
        #         j.builders.tools.file_copy('{code}/{item}'.format(code=codedir, item=item), bindir+'/')
        #     return
        # j.core.tools.dir_ensure(self.DIR_BUILD)
        # cmd = "cd {code} && DESTDIR={build} make install".format(code=codedir, build=self.DIR_BUILD)
        # j.sal.process.execute(cmd)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.network.zerotier.install()'
        :return:
        """
        self._copy("{DIR_BUILD}/usr/sbin/", "{DIR_BASE}/bin/")

    @property
    def startup_cmds(self):
        cmd = j.servers.startupcmd.get("zerotier", "zerotier-one", path="/tmp", timeout=10, ports=[9993])
        return [cmd]

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=True, merge_base_flist=""):

        """Copy built bins to dest_path and create flist
        """
        zt_bin_path = self._joinpaths("{DIR_BIN}", "zerotier-one")
        bin_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "bin")
        self._dir_ensure(bin_dest)
        self._copy(zt_bin_path, bin_dest)

    def test(self):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self.start()
        self.stop()
        print("TEST OK")
