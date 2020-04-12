from Jumpscale import j

builder_method = j.baseclasses.builder_method


class BuilderZola(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.zola"

    def _init(self):
        self.RELEASE_VERSION = "v0.10.1"

    @builder_method()
    def build(self):
        """
        kosoms 'j.builders.apps.zola.build()'
        """

        self._execute(
            "cd {DIR_TEMP}; wget -c https://github.com/getzola/zola/releases/download/%s"
            "/zola-%s-x86_64-unknown-linux-gnu.tar.gz" % (self.RELEASE_VERSION, self.RELEASE_VERSION) 
        )
        self._execute("cd {DIR_TEMP}; tar -xvzf zola-%s-x86_64-unknown-linux-gnu.tar.gz" % self.RELEASE_VERSION)

    @builder_method()
    def install(self, reset=False):
        """
        kosmos  'j.builders.apps.zola.install()'
        :param reset:
        :return:
        """

        if not reset and j.sal.fs.exists("{DIR_BIN}/zola"):
            return
        if reset:
            self._remove("{DIR_BIN}/zola")
        self._copy("{DIR_TEMP}/zola", "{DIR_BIN}")

    def clean(self):
        self._remove("{DIR_TEMP}/zola")
        self._remove("{DIR_TEMP}/zola-%s-x86_64-unknown-linux-gnu.tar.gz" % self.RELEASE_VERSION)

    def reset(self):
        super().reset()
        self.clean()
        self._remove("{DIR_BIN}/zola")
