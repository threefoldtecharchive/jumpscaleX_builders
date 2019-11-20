from Jumpscale import j
import textwrap

builder_method = j.baseclasses.builder_method


class BuilderHub(j.baseclasses.builder):

    __jslocation__ = "j.builders.apps.zerohub"

    def _init(self, **kwargs):
        self.DIR_CODE = self._joinpaths(self.DIR_BUILD, "code")
        self.MAKEOPTS = "-j 5"
        self.DEST_CURL = self._joinpaths(self.DIR_CODE, "curl")
        self.DEST_CAPNP = self._joinpaths(self.DIR_CODE, "capnp")
        self.DEST_HUB = self._joinpaths(self.DIR_CODE, "hub")
        self.DEST_ZEROFLIST = self._joinpaths(self.DIR_CODE, "zeroflist")
        self.HUB_SANDBOX = self._joinpaths(self.DIR_SANDBOX, "sandbox")
        self._dir_ensure(self.HUB_SANDBOX)
        self.DEST_SANDBOX_HUB = self._joinpaths(self.DIR_SANDBOX, "sandbox", "hub")
        self.DEST_SANDBOX_ZEROFLIST = self._joinpaths(self.DIR_SANDBOX, "sandbox", "zeroflist")

    @builder_method()
    def clean(self):
        self._remove(self.DIR_CODE)
        self._remove(self.HUB_SANDBOX)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def in_docker(self, docker_ip):
        """
        for testing purposes just pass your docker ip to this method
        to set it to environment variables
        """
        self.profile.env_set_part("IP_PORT", docker_ip)

    @builder_method()
    def build(self):
        # install dependancies
        self.system.package.mdupdate()
        self.system.package.install(
            [
                "build-essential",
                "git",
                "libsnappy-dev",
                "libz-dev",
                "libtar-dev",
                "libb2-dev",
                "autoconf",
                "libtool",
                "libjansson-dev",
                "libhiredis-dev",
                "libsqlite3-dev",
                "tmux",
                "vim",
                "python3-flask",
                "python3-redis",
                "python3-docker",
                "python3-pytoml",
                "python3-jwt",
                "libssl-dev",
            ]
        )
        # zdb backend
        j.builders.db.zdb.install()

        # libcurl build
        curl_url = "https://github.com/curl/curl"
        j.clients.git.pullGitRepo(dest=self.DEST_CURL, url=curl_url, depth=1, branch="curl-7_62_0")

        curl_cmd = """
        rm -f /usr/local/lib/libcurl.so.*
        cd {DEST_CURL}
        autoreconf -f -i -s
        ./configure --disable-debug --enable-optimize --disable-curldebug --disable-symbol-hiding --disable-rt \
        --disable-ftp --disable-ldap --disable-ldaps --disable-rtsp --disable-proxy --disable-dict \
        --disable-telnet --disable-tftp --disable-pop3 --disable-imap --disable-smb --disable-smtp --disable-gopher \
        --disable-manual --disable-libcurl-option --disable-sspi --disable-ntlm-wb --without-brotli --without-librtmp --without-winidn \
        --disable-threaded-resolver \
        --with-openssl
        make {MAKEOPTS}
        make install
        make install DESTDIR="{DIR_BASE}/"
        ldconfig
        """
        self._execute(curl_cmd)

        # capnp builder
        capnp_url = "https://github.com/opensourcerouting/c-capnproto"
        j.clients.git.pullGitRepo(dest=self.DEST_CAPNP, url=capnp_url, depth=1)

        capnp_cmd = """
        cd {DEST_CAPNP}
        git submodule update --init --recursive
        autoreconf -f -i -s
        ./configure
        make {MAKEOPTS}
        make install
        make install DESTDIR="{DIR_BASE}/"
        ldconfig
        """
        self._execute(capnp_cmd)

        # zeroflist
        zeroflist_url = "https://github.com/threefoldtech/0-flist/"
        j.clients.git.pullGitRepo(dest=self.DEST_ZEROFLIST, url=zeroflist_url, depth=1, branch="development")

        zeroflist_cmd = """
        cd {DEST_ZEROFLIST}
        pushd libflist
        make
        popd
        pushd zflist
        make production DESTDIR="{DIR_BASE}/"
        popd
        cp zflist/zflist /tmp/zflist
        strip -s /tmp/zflist
        """
        self._execute(zeroflist_cmd)

        # hub
        hub_url = "https://github.com/threefoldtech/0-hub"
        j.clients.git.pullGitRepo(dest=self.DEST_HUB, url=hub_url, depth=1, branch="playground")

    @builder_method()
    def install(self):
        # install hub
        file_src = self._joinpaths(j.sal.fs.getDirName(__file__), "templates", "zerohub_config.py")
        file_dest = self._joinpaths(self.DEST_HUB, "python", "config.py")
        self._copy(file_src, file_dest)
        self._execute(
            """
            sed -i "s/\\"zflist-bin\\": \\"\/opt\/0-flist\/zflist\/zflist\\"/\\"zflist-bin\\":\
                 \\"\/tmp\/builders\/zerohub\/code\/zeroflist\/zflist\/zflist\\"/" {DEST_HUB}/python/config.py
        """
        )

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None, flist_create=False):
        # ensure dirs
        bin_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "bin")
        self._dir_ensure(bin_dest)

        # sandbox zdb
        bins = ["zdb"]
        for bin in bins:
            self._copy("{DIR_BIN}/" + bin, bin_dest)

        lib_dest = self._joinpaths(self.DIR_SANDBOX, "sandbox", "lib")
        self._dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self._joinpaths(bin_dest, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest)

        # sandbox curl
        curl_install_cmd = """
        cd {DEST_CURL}
        make install DESTDIR={HUB_SANDBOX}
        ldconfig
        """
        self._execute(curl_install_cmd)

        # sandbox capnp
        capnp_sandbox_cmd = """
        cd {DEST_CAPNP}
        make install DESTDIR={HUB_SANDBOX}
        ldconfig
        """
        self._execute(capnp_sandbox_cmd)

        # sandbox zflist
        self._copy(self.DEST_ZEROFLIST, self.DEST_SANDBOX_ZEROFLIST)
        # sandbox hub
        self._copy(self.DEST_HUB, self.DEST_SANDBOX_HUB)

        # install hub
        file_src = self._joinpaths(j.sal.fs.getDirName(__file__), "templates", "zerohub_config.py")
        file_dest = self._joinpaths(self.DEST_SANDBOX_HUB, "python", "config.py")
        self._copy(file_src, file_dest)
        self._execute(
            """
            sed -i "s/\\"zflist-bin\\": \\"\/opt\/0-flist\/zflist\/zflist\\"/\\"zflist-bin\\":\
            \\"\{DIR_BASE}\/zeroflist\/zflist\/zflist\\"/" {DEST_SANDBOX_HUB}/python/config.py
        """
        )

        file = self._joinpaths(j.sal.fs.getDirName(__file__), "templates", "zerohub_startup.toml")
        file_dest = self._joinpaths(self.DIR_SANDBOX, ".startup.toml")
        self._copy(file, file_dest)

    @property
    def startup_cmds(self):

        j.builders.db.zdb.start()
        start_script = self._replace(
            """
        cd {DIR_CODE}/hub/python/ && python3 flist-uploader.py
        """
        )
        start_cmd = j.servers.startupcmd.get(self._name, cmd_start=start_script)
        return [start_cmd]

    @builder_method()
    def stop(self):
        # killing the daemon
        j.servers.tmux.pane_get(self._name).kill()
        j.builders.db.zdb.stop()

    @builder_method()
    def test(self):
        if self.running():
            self.stop()
        self.start()
        assert self.running()
        self.stop()
        print("TEST OK")
