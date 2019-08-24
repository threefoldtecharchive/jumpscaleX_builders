from Jumpscale import j
import os
import textwrap


class BuilderMicroEditor(j.builders.system._BaseClass):
    NAME = "micro"

    def install(self, reset=False):
        """
        """

        if self._done_check("install", reset):
            return

        print("INSTALL MICROEDITOR")

        if j.core.platformtype.myplatform.platform_is_osx:
            url = "https://github.com/zyedidia/micro/releases/download/v1.3.3/micro-1.3.3-osx.tar.gz"
        elif j.core.platformtype.myplatform.platform_is_ubuntu:
            url = "https://github.com/zyedidia/micro/releases/download/v1.3.3/micro-1.3.3-linux64.tar.gz"
        else:
            raise j.exceptions.Base("not implemented for other platforms")

        dest = j.builders.network.tools.download(
            url=url, to="{DIR_TEMP}/micro/", overwrite=False, retry=3, expand=True, removeTopDir=True
        )
        j.builders.tools.file_move("{DIR_TEMP}/micro/micro", "/usr/local/bin/micro", recursive=False)

        self._done_set("install")
