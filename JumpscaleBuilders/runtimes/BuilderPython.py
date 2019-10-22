from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderPython(j.baseclasses.builder):
    """
    : Determine version using
    : > j.builders.runtimes.python3.TAG = "vX.Y.Z"
    """

    __jslocation__ = "j.builders.runtimes.python3"
    TAG = "v3.6.8"

    def _init(self, **kwargs):

        self.DIR_CODE_L = self.tools.joinpaths(self.DIR_BUILD, "code/")
        self.tools.dir_ensure(self.DIR_CODE_L)

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.runtimes.python3.build()'
            kosmos 'j.builders.runtimes.python3.build(reset=True)'
        will build python
        :param reset: choose to reset the build process even if it was done before
        :type reset: bool
        :return:
        """
        # install dependancies and build tools
        j.builders.libs.cmake.install()
        self.system.package.mdupdate()
        self._execute("apt-get update")
        self.system.package.install(
            [
                "build-essential",
                "git",
                "libexpat1-dev",
                "libssl-dev",
                "zlib1g-dev",
                "libncurses5-dev",
                "libbz2-dev",
                "liblzma-dev",
                "libsqlite3-dev",
                "libffi-dev",
                "libreadline-dev",
                "dialog",
            ]
        )
        self._execute(
            """
        export DEBIAN_FRONTEND=noninteractive
        apt-get install tk tk-dev linux-headers-generic tcl-dev libgdbm-dev -yq
        """
        )
        python_url = "https://github.com/python/cpython.git"

        build_cmd = """
        cd {code}
        rm -rf cpython
        git clone --depth 1 --branch {tag} {python_url}
        cd cpython
        ./configure --prefix=""
        make -j4
        """.format(
            code=self.DIR_CODE_L, python_url=python_url, tag=self.TAG
        )
        self._execute(build_cmd)

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.runtimes.python3.install()'
        """
        install_cmd = """
        cd {DIR_CODE_L}/cpython
        make install DESTDIR=/sandbox
        """.format(
            DIR_CODE_L=self.DIR_CODE_L
        )
        self._execute(install_cmd)
        self.build_pip()

    @builder_method()
    def build_pip(self):
        """
        kosmos 'j.builders.runtimes.python3.build_pip()'
        :return:
        """
        # test openssl is working
        cmd = "python3 -c 'import ssl'"
        rc, _, err = self._execute(cmd, die=False)
        if rc > 0:
            raise j.exceptions.Base("SSL was not included in building process !\n%s" % err)
        self._pip_install()
        self._pip_packages_all()

    @builder_method()
    def _pip_install(self):
        """
        kosmos 'j.builders.runtimes.python3._pip_install()'
        will make sure we add env scripts to it as well as add all the required pip modules
        """
        script = """
        apt-get -f install
        rm -rf get-pip.py
        curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
        python3 get-pip.py
        python3 -m pip install -U pip
        """
        self._execute(script)

    @builder_method()
    def _pip_packages_all(self):
        """
        kosmos 'j.builders.runtimes.python3._pip_packages_all()'
        """
        j.builders.libs.capnp.install(reset=True)
        # list comes from /sandbox/code/github/threefoldtech/jumpscale_core/install/InstallTools.py
        self.pip_package_install(j.core.installer_base.pips_list(0))

        # get the zerohub client
        self._execute("pip3 install -e 'git+https://github.com/threefoldtech/0-hub#egg=zerohub&subdirectory=client'")

        self._log_info("PIP DONE")

    @builder_method()
    def pip_package_install(self, pips):
        pips = j.core.text.getList(pips, "str")
        if len(pips) == 1:
            self._execute(
                "pip3 install --trusted-host pypi.python.org '{PACKAGE}' --upgrade", args={"PACKAGE": pips[0]}
            )
        else:
            for item in pips:
                self.pip_package_install(item)

    @builder_method()
    def pip_package_uninstall(self, package):
        """
        The "package" argument, defines the name of the package that will be ensured.
        """
        self.ensure()
        packages = j.core.text.getList(package, "str")
        if len(packages) == 1:
            return j.sal.process.execute("pip3 uninstall %s" % (packages[0]))
        else:
            for package in packages:
                self.pip_package_uninstall(package)

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """
        kosmos 'j.builders.runtimes.python3.sandbox()'

        Copy built bins to dest_path and create flist if create_flist = True
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
        sandbox_cmd = """
        cd {DIR_CODE_L}/cpython
        make install DESTDIR={DIR_SANDBOX}
        """.format(
            DIR_CODE_L=self.DIR_CODE_L, DIR_SANDBOX=sandbox_dir
        )
        self._execute(sandbox_cmd)
        self.build_pip()
        self.PACKAGE_DIR = self._replace("{DIR_SANDBOX}/sandbox")
        bins_dir = self._replace("{PACKAGE_DIR}/bin")
        j.tools.sandboxer.libs_clone_under(bins_dir, sandbox_dir)

    @builder_method()
    def clean(self):
        self._remove(self.DIR_CODE_L)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def test(self):
        """
        js_shell 'j.builders.runtimes.python3.test(build=True)'
        """
        self.profile_builder_select()
        assert self._execute("python3 -c \"print('python')\"")[1] == "python\n"
        assert self._execute('python3 -c "import capnp"')[0] == 0
        assert self._execute('python3 -c "import ssl"')[0] == 0

        print("TEST OK")
