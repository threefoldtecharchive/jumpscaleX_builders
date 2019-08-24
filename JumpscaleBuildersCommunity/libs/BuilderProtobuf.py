from Jumpscale import j


class BuilderProtobuf(j.builders.system._BaseClass):

    NAME = "protoc"

    def install(self, reset=False):
        """
        install protobut
        """
        if self._done_check("install", reset):
            return

        j.builders.system.package.mdupdate()
        if j.core.platformtype.myplatform.platform_is_osx:
            j.builders.system.package.ensure(["protobuf"])
        else:
            url = "https://github.com/google/protobuf/releases/download/v3.4.0/protoc-3.4.0-linux-x86_64.zip"
            res = j.builders.network.tools.download(
                url, to="", overwrite=False, retry=3, timeout=0, expand=True, removeTopDir=False
            )
            j.builders.tools.file_move("%s/bin/protoc" % res, "/usr/local/bin/protoc")
        j.builders.system.python_pip.install("protobuf3", upgrade=True)  # why not protobuf?

        self._done_set("install")
