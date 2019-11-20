from Jumpscale import j
import os


class BuilderLedis(j.baseclasses.builder):
    __jslocation__ = "j.builders.db.ledis"

    def build(self, backend="leveldb", install=True, start=True, reset=False):
        if self._done_check("build", reset):
            return

        if j.core.platformtype.myplatform.platform_is_ubuntu:

            C = """
            #!/bin/bash
            set -x

            cd {ledisdir}
            #set build and run environment
            source dev.sh

            make
            """
            j.builders.runtimes.go.install()
            j.clients.git.pullGitRepo(
                "https://github.com/siddontang/ledisdb", dest="{DIR_BASE}/go/src/github.com/siddontang/ledisdb"
            )

            # set the backend in the server config
            ledisdir = self._replace("{DIR_BASE}/go/src/github.com/siddontang/ledisdb")

            configcontent = j.core.tools.file_text_read(os.path.join(ledisdir, "config", "config.toml"))
            ledisdir = self._replace("{DIR_BASE}/go/src/github.com/siddontang/ledisdb")

            if backend == "rocksdb":
                self._preparerocksdb()
            elif backend == "leveldb":
                rc, out, err = self._prepareleveldb()
            else:
                raise j.exceptions.NotImplemented
            configcontent.replace('db_name = "leveldb"', 'db_name = "%s"' % backend)

            self._write("/tmp/ledisconfig.toml", configcontent)

            script = C.format(ledisdir=ledisdir)
            out = j.sal.process.execute(script, profile=True)

            if install:
                self.install(start=True)

            self._done_set("build")

    def _prepareleveldb(self):
        # execute the build script in tools/build_leveldb.sh
        # it will install snappy/leveldb in /usr/local{snappy/leveldb} directories
        ledisdir = self._replace("{DIR_BASE}/go/src/github.com/siddontang/ledisdb")
        # leveldb_build file : ledisdir/tools/build_leveldb.sh
        rc, out, err = j.sal.process.execute("bash {ledisdir}/tools/build_leveldb.sh".format(ledisdir=ledisdir))
        return rc, out, err

    def _preparerocksdb(self):
        raise j.exceptions.NotImplemented

    def install(self, start=True):
        if self._done_check("install", reset):
            return

        ledisdir = self._replace("{DIR_BASE}/go/src/github.com/siddontang/ledisdb")

        # rc, out, err = j.sal.process.execute("cd {ledisdir} && source dev.sh && make install".format(ledisdir=ledisdir), profile=True)
        j.core.tools.dir_ensure("{DIR_VAR}/templates/cfg")
        j.builders.tools.file_copy("/tmp/ledisconfig.toml", dest="{DIR_VAR}/templates/cfg/ledisconfig.toml")
        j.builders.tools.file_copy("{ledisdir}/bin/*".format(ledisdir=ledisdir), dest="{DIR_BIN}")
        j.builders.tools.file_copy(
            "{ledisdir}/dev.sh".format(ledisdir=ledisdir), dest="{DIR_VAR}/templates/ledisdev.sh"
        )

        self._done_set("install")

        if start:
            self.start()

    def start(self):
        cmd = "source {DIR_VAR}/templates/ledisdev.sh && {DIR_BIN}/ledis-server -config {DIR_VAR}/templates/cfg/ledisconfig.toml"
        pm = j.builders.system.processmanager.get("tmux")
        pm.ensure(name="ledis", cmd=cmd)
