from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderIodide(j.baseclasses.builder):
    """
    """

    __jslocation__ = "j.builders.runtimes.iodide"

    @builder_method()
    def build(self):
        """
        kosmos 'j.builders.runtimes.iodide.build()'
        kosmos 'j.builders.runtimes.iodide.build(reset=True)'

        will build iodide
        :param reset: choose to reset the build process even if it was done before
        :type reset: bool
        :return:
        """
        if self.tools.platform_is_linux:
            raise RuntimeError("not supported yet, TODO:*1")
            j.builders.libs.cmake.install()
            self.system.package.mdupdate()
        if self.tools.platform_is_osx:
            self.system.package.install(["pkg-config", "openssl", "wget", "coreutils", "ccache"])
            self._execute("brew cask install gfortran")
            self._execute("brew cask install f2c")

        build_cmd = """
        cd {DIR_TEMP}
        rm -rf pyodide
        git clone --depth 1 git@github.com:iodide-project/pyodide.git
        cd pyodide
        sudo ./tools/buildf2c
        sudo npm install less --global
        sudo npm install -g uglify-js
        make
        """
        self._execute(build_cmd)

    # @builder_method()
    # def install(self):
    #     """
    #     kosmos 'j.builders.runtimes.iodide.install()'
    #     """
    #     install_cmd = (
    #         """
    #     cd %s/ciodide
    #     make install DESTDIR={DIR_BASE}
    #     """
    #         % self.DIR_CODE_L
    #     )
    #     self._execute(install_cmd)
    #     self.build_pip()

    @builder_method()
    def test(self):
        """
        js_shell 'j.builders.runtimes.iodide.test(build=True)'
        """
        self.profile_builder_select()

        print("TEST OK")
