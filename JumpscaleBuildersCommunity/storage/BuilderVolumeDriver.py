from Jumpscale import j
from time import sleep


class BuilderVolumeDriver(j.baseclasses.builder):
    __jslocation__ = "j.builders.storage.volumedriver"

    def build(self, reset=False):
        if reset is False and self.isInstalled():
            return
        self._install_deps()
        self._build()

    def _install_deps(self):
        self._write("/etc/apt/sources.list.d/ovsaptrepo.list", "deb http://apt.openvstorage.org unstable main")
        j.sal.process.execute(
            'echo "deb http://us.archive.ubuntu.com/ubuntu xenial main universe" >> /etc/apt/sources.list'
        )
        j.builders.system.package.mdupdate()
        j.builders.system.package.upgrade(distupgrade=True)

        apt_deps = """
        gcc g++ clang-3.8 valgrind \
        libboost1.58-all-dev \
        build-essential sudo \
        flex bison gawk check pkg-config \
        autoconf libtool realpath bc gettext lcov \
        unzip doxygen dkms debhelper pylint git cmake \
        wget libssl-dev libpython2.7-dev libxml2-dev \
        libcurl4-openssl-dev libc6-dbg liblz4-dev \
        librabbitmq-dev libaio-dev libkrb5-dev libc-ares-dev \
        pkg-create-dbgsym elfutils \
        libloki-dev libprotobuf-dev liblttng-ust-dev libzmq3-dev \
        libtokyocabinet-dev libbz2-dev protobuf-compiler \
        libgflags-dev libsnappy-dev \
        redis-server libhiredis-dev libhiredis-dbg \
        libomniorb4-dev omniidl omniidl-python omniorb-nameserver \
        librdmacm-dev libibverbs-dev python-nose fuse \
        python-protobuf \
        supervisor rpcbind \
        libxio0 libxio-dev libev4
        """
        j.builders.system.package.ensure(apt_deps, allow_unauthenticated=True)

    def _build(self, version="6.0.0"):
        workspace = self._replace("{DIR_TEMP}/volumedriver-workspace")
        j.core.tools.dir_ensure(workspace)

        str_repl = {"workspace": workspace, "version": version}

        str_repl["volumedriver"] = j.clients.git.pullGitRepo("https://github.com/openvstorage/volumedriver", depth=None)
        str_repl["buildtools"] = j.clients.git.pullGitRepo(
            "https://github.com/openvstorage/volumedriver-buildtools", depth=None
        )
        j.sal.process.execute("cd %(volumedriver)s;git checkout tags/%(version)s" % str_repl)

        j.builders.tools.file_link(str_repl["buildtools"], self._joinpaths(workspace, "volumedriver-buildtools"))
        j.builders.tools.file_link(str_repl["volumedriver"], self._joinpaths(workspace, "volumedriver"))

        build_script = (
            """
        export WORKSPACE=%(workspace)s
        export RUN_TESTS=no


        cd ${WORKSPACE}/volumedriver-buildtools/src/release/
        ./build-jenkins.sh

        cd ${WORKSPACE}
        ./volumedriver/src/buildscripts/jenkins-release-dev.sh ${WORKSPACE}/volumedriver
        """
            % str_repl
        )

        j.sal.process.execute(build_script)
        j.builders.tools.file_copy("{DIR_TEMP}/volumedriver-workspace/volumedriver/build/bin/*", "{DIR_BIN}")
