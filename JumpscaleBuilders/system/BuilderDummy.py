from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderDummy(j.builders.system._BaseClass):
    NAME = "dummy"

    @builder_method()
    def _init(self, **kwargs):
        self.variable = "value"
        self._log_debug("init_ called")

    @builder_method()
    def build(self, reset=False):
        self._log_debug("build called reset=%s" % reset)

    @builder_method()
    def install(self, reset=False):
        self._log_debug("install called")

    @builder_method()
    def sandbox(self, zhub_client=None):
        self._log_debug("sandbox called with zhubclient=%s" % zhub_client)
