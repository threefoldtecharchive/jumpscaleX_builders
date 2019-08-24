from Jumpscale import j

JSBASE = j.builders.system._BaseClass
builder_method = j.builders.system.builder_method


class BuilderRipple(JSBASE):
    NAME = "rippled"

    @builder_method()
    def build(self):
        """Get/Build the binaries of ripple
        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
            # rfer to: https://ripple.com/build/rippled-setup/#installing-rippled
        """
        # Prerequisites build tools
        self.system.package.mdupdate()
        self.system.package.install(
            [
                "git",
                "pkg-config",
                "protobuf-compiler",
                "libprotobuf-dev",
                "libssl-dev wget",
                "python-dev",
                "python3-dev",
            ]
        )

        # install cmake
        j.builders.libs.cmake.install()

        # rippled requires Boost to be compiled
        boost_build_cmd = """
            cd {DIR_BUILD}
            wget https://dl.bintray.com/boostorg/release/1.67.0/source/boost_1_67_0.tar.gz
            tar xvzf boost_1_67_0.tar.gz
            cd boost_1_67_0
            ./bootstrap.sh
            ./b2 -j 4 -q
            export BOOST_ROOT={DIR_BUILD}/boost_1_67_0
            echo "finished"
        """
        self._execute(boost_build_cmd, timeout=5000)

        # clone and build ripple
        ripple_build_cmd = """
            cd {DIR_BUILD}
            rm -rf rippled
            git clone https://github.com/ripple/rippled.git
            cd rippled
            git checkout master
            mkdir my_build
            cd my_build
            export BOOST_ROOT={DIR_BUILD}/boost_1_67_0
            cmake .. -DCMAKE_BUILD_TYPE=Release
            cmake --build .
        """
        self._execute(ripple_build_cmd, timeout=4000)

        # ripple configuration
        config_cmd = """
            mkdir -p ~/.config/ripple
            cd {DIR_BUILD}/rippled/
            cp cfg/rippled-example.cfg ~/.config/ripple/rippled.cfg
            cp cfg/validators-example.txt ~/.config/ripple/validators.txt
        """
        self._execute(config_cmd)

    @builder_method()
    def install(self):
        # copy bins to DIR_BIN
        self._copy("{DIR_BUILD}/rippled/my_build/rippled", "{DIR_BIN}")

    @builder_method()
    def sandbox(self, zhub_client=None, flist_create=True, merge_base_flist=""):
        # copy bins to DIR_BIN
        bin_dest = j.sal.fs.joinPaths(self.DIR_SANDBOX, "sandbox", "bin")
        self.tools.dir_ensure(bin_dest)
        self._copy("{DIR_BIN}/rippled", bin_dest)

    @builder_method()
    def clean(self):
        code_dir = j.sal.fs.joinPaths(self.DIR_BUILD, "rippled")
        self._remove(code_dir)

    @property
    def startup_cmds(self):
        cmd = "/sandbox/bin/{}".format(self.NAME)
        cmds = [j.servers.startupcmd.get(name=self.NAME, cmd_start=cmd)]
        return cmds

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def stop(self):
        j.sal.process.killProcessByName(self.NAME)

    @builder_method()
    def test(self):
        if self.running():
            self.stop()

        self.start()
        assert self.running()
        print("TEST OK")
