from Jumpscale import j
import os
import textwrap


class BuilderDuplicacy(j.baseclasses.builder):
    __jslocation__ = "j.builders.storage.duplicacy"

    def build(self, reset=False, install=False):
        """
        Builds duplicacy

        @param reset boolean: forces the build operation.
        """
        if self._done_check("build", reset):
            return

        dup_url = "https://github.com/gilbertchen/duplicacy/releases/download/v2.0.10/duplicacy_linux_x64_2.0.10"
        j.builders.tools.file_download(dup_url, overwrite=True, to="{DIR_TEMP}/duplicacy")
        self._done_set("build")

        if install:
            self.install(False)

    def install(self, reset=False, start=False):
        """
        Installs duplicacy

        @param reset boolean: forces the install operation.
        """
        if self._done_check("install", reset):
            return
        j.sal.process.execute("cp {DIR_TEMP}/duplicacy {DIR_BIN}/")
        self._done_set("install")

        if start:
            self.start()

    def start(self, name="main"):
        """
        Starts duplicacy.
        """
        pass

    def stop(self, name="main"):
        """
        Stops duplicacy 
        """

        pass

    def restart(self, name="main"):
        self.stop(name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        pass
