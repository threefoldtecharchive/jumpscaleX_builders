from Jumpscale import j


class BuilderFuse(j.baseclasses.builder):
    __jslocation__ = "j.builders.storage.fuse"

    def install(self):
        j.builders.system.package.ensure(
            [
                "python3.5",
                "python3-pkgconfig",
                "pkg-config",
                "libfuse-dev",
                "libattr1-dev",
                "python3-llfuse",
                "python3-setuptools",
                "python3-dev",
            ]
        )

        LLFUSE_URL = "https://pypi.python.org/packages/c2/dc/a3cb7417daf34b6021aac0bb1a1ad51cf24fc3264ba5a68ab71349d79dd6/llfuse-1.1.1.tar.bz2#md5=61a427d5074d2804d259c5bc2f1965b3"
        CMD = """
        set -ex
        cd {DIR_TEMP}/
        wget {LLFUSE_URL}
        tar xf llfuse-1.1.1.tar.bz2
        cd llfuse-1.1.1
        python3 setup.py install
        """.format(
            LLFUSE_URL=LLFUSE_URL
        )
        j.sal.process.execute(self._replace(CMD))
