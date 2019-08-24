from Jumpscale import j
from .GrafanaComponent import GrafanaComponent


class BuilderGrafanaFactory(j.builders.system._BaseFactoryClass):

    __jslocation__ = "j.builders._template"
    _CHILDCLASS = GrafanaComponent

    def build(self):
        # dont use prefab (can copy code from there for sure)
        # check is ubuntu (ONLY SUPPORT UBUNTU 18.04)
        # build (if relevant) or install on local machine
        def do():
            pass

        self._cache.get(key="build", method=do, expire=3600 * 30 * 24, refresh=False, retry=2, die=True)

    def sandbox(self):
        # copy relevant files to the sandbox
        # call the sandboxer to get the right libs in the sandbox (if relevant)
        # can call other servers build/sandbox
        # sandboxing  makes sure that all relevant files are in the sandbox, does not do any configuration
        def do():
            pass

        self._cache.get(key="sandbox", method=do, expire=3600 * 30 * 24, refresh=False, retry=1, die=True)

    def client_get(self, name):
        """
        return the client to the installed server, use the config params of the server to create a client for
        :return:
        """
        s = self.get(name)
        # client = j.clients.grafana.get(name=name, addr=s....)
        return client

    def test(self):
        """

        kosmos 'j.builders._template.test()'

        :return:
        """
        # TODO: check that test instance is running, if so stop
        # TODO: build/sandbox a server (or component)
        # TODO: call the component call start/stop/... to test
        # TODO: create a client to the server (use j.clients....) and connect to server if a server
        # TODO: do some test on the server (use the component.test... method)
        pass
