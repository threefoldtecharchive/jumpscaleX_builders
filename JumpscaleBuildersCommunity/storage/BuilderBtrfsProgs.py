from Jumpscale import j
from JumpscaleBuilder.BuilderFactory import BuilderApp


class BuilderBtrfsProgs(BuilderApp):
    __jslocation__ = "j.builders.storage.btrfs"

    # depends of: pkg-config build-essential e2fslibs-dev libblkid-dev liblzo2-dev

    def _init(self, **kwargs):
        # if the module builds something, define BUILDDIR and CODEDIR folders.
        self.BUILDDIR = self._replace("{DIR_VAR}/build/btrfs-progs/")
        self.CODEDIR = self._replace("{DIR_CODE}")

        self._host = "https://www.kernel.org/pub/linux/kernel/people/kdave/btrfs-progs"
        self._file = "btrfs-progs-v4.8.tar.xz"

    def _run(self, command):
        return j.sal.process.execute(self._replace(command))

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        j.sal.fs.remove(self.BUILDDIR)
        j.sal.fs.remove(self.CODEDIR + "btrfs-progs-v4.8")
        self.doneDelete("build")
        self._run("cd $LIBDIR; rm -f libbtrfs.so.0.1")
        self._run("cd $LIBDIR; rm -f libbtrfs.so.0")
        self._run("rm -f {DIR_BIN}/btrfs")
        j.builders.system.python_pip.reset()

    def build(self, reset=False):
        if reset is False and (self.isInstalled() or self._done_get("build")):
            return
        self._execute("apt-get -y install asciidoc xmlto --no-install-recommends")
        deps = """
        uuid-dev libattr1-dev zlib1g-dev libacl1-dev e2fslibs-dev libblkid-dev liblzo2-dev autoconf
        """
        j.builders.system.package.ensure(deps)
        self._run("cd {DIR_TEMP}; wget -c %s/%s" % (self._host, self._file))
        self._run("cd {DIR_TEMP}; tar -xf %s -C {CODEDIR}" % self._file)
        self._run("cd {CODEDIR}/btrfs-progs-v4.8; ./autogen.sh")
        self._run("cd {CODEDIR}/btrfs-progs-v4.8; ./configure --prefix={DIR_VAR}/build/ --disable-documentation")
        self._run("cd {CODEDIR}/btrfs-progs-v4.8; make")
        self._run("cd {CODEDIR}/btrfs-progs-v4.8; make install")

        self._done_set("build")

    def install(self, reset=False):
        # copy binaries, shared librairies, configuration templates,...
        j.builders.tools.file_copy(self._replace("{DIR_VAR}/build/bin/btrfs"), "{DIR_BIN}")

        j.builders.tools.file_copy(self._replace("{DIR_VAR}/build/lib/libbtrfs.so"), "$LIBDIR")
        self._run("cd $LIBDIR; ln -sf libbtrfs.so libbtrfs.so.0.1")
        self._run("cd $LIBDIR; ln -sf libbtrfs.so libbtrfs.so.0")

    def start(self, name):
        pass

    def stop(self, name):
        pass

    def getClient(self, executor=None):
        return j.sal.btrfs.getBtrfs(executor)
