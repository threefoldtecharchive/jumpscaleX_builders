from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderMdbook(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.mdbook"

    def _init(self):
        self.RELEASE_VERSION = "v0.3.7"

    @builder_method()
    def build(self):
        """
        kosoms 'j.builders.apps.mdbook.build()'
        """

        self._execute(
            "cd {DIR_TEMP}; wget -c https://github.com/rust-lang/mdBook/releases/download/%s"
            "/mdbook-%s-x86_64-unknown-linux-gnu.tar.gz" % (self.RELEASE_VERSION, self.RELEASE_VERSION) 
        )
        self._execute("cd {DIR_TEMP}; tar -xvzf mdbook-%s-x86_64-unknown-linux-gnu.tar.gz" % self.RELEASE_VERSION)

    @builder_method()
    def install(self, reset=False):
        """
        kosmos  'j.builders.apps.mdbook.install()'
        :param reset:
        :return:
        """

        if not reset and j.sal.fs.exists("{DIR_BIN}/mdbook"):
            return
        if reset:
            self._remove("{DIR_BIN}/mdbook")
        self._copy("{DIR_TEMP}/mdbook", "{DIR_BIN}")

    def clean(self):
        self._remove("{DIR_TEMP}/mdbook")
        self._remove("{DIR_TEMP}/mdbook-%s-x86_64-unknown-linux-gnu.tar.gz" % self.RELEASE_VERSION)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()
        self._remove("{DIR_BIN}/mdbook")

    @builder_method()
    def uninstall(self):
        if self.running():
            self.stop()
        self._remove("{DIR_BIN}/mdbook")
