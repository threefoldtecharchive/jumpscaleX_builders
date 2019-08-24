from Jumpscale import j

builder_method = j.builders.system.builder_method


class BuilderTraefik(j.baseclasses.builder):
    __jslocation__ = "j.builders.web.traefik"
    VERSION = "1.7.9"  # latest
    URL = "https://github.com/containous/traefik/releases/download/v{version}/traefik_{platform}-{arch}"

    def _init(self, **kwargs):

        self.go_runtime = j.builders.runtimes.golang

    @builder_method()
    def install(self):
        """

        kosmos 'j.builders.web.traefik.install()'

        """
        version = tuple(map(int, self.go_runtime.STABLE_VERSION.split(".")))
        if version < (1, 9):
            raise j.exceptions.RuntimeError("%s requires go version >= 1.9")

        # get the prebuilt binary, as the building needs docker...etc
        # only check for linux for now
        arch = self.go_runtime.current_arch
        if j.core.platformtype.myplatform.platform_is_linux:
            download_url = self.URL.format(version=self.VERSION, platform="linux", arch=arch)
        else:
            raise j.exceptions.RuntimeError("platform not supported")

        dest = self.tools.joinpaths(self._replace("{DIR_BIN}"), self.NAME)
        self.tools.file_download(download_url, dest, overwrite=True, retry=3, timeout=0)
        self.tools.file_attribs(dest, mode=0o770)

    def start(self, config_file=None, args=None):
        """Starts traefik with the configuration file provided

        :param config_file: config file path e.g. ~/traefik.toml
        :type config_file: str, optional
        :param args: any additional arguments to be passed to traefik
        :type args: dict, optional (e.g. {'api': '', 'api.dashboard': 'true'})
        :raises j.exceptions.RuntimeError: in case config file does not exist
        :return: tmux pane
        :rtype: tmux.Pane
        """
        cmd = self.tools.joinpaths(self._replace("{DIR_BIN}"), self.NAME)
        if config_file and self.tools.file_exists(config_file):
            cmd += " --configFile=%s" % config_file

        args = args or {}
        for arg, value in args.items():
            cmd += " --%s" % arg
            if value:
                cmd += "=%s" % value

        p = j.servers.tmux.execute(cmd, window=self.NAME, pane=self.NAME, reset=True)
        return p

    def stop(self, pid=None, sig=None):
        """Stops traefik process

        :param pid: pid of the process, if not given, will kill by name
        :type pid: long, defaults to None
        :param sig: signal, if not given, SIGKILL will be used
        :type sig: int, defaults to None
        """
        if pid:
            j.sal.process.kill(pid, sig)
        else:
            j.sal.process.killProcessByName(self.NAME, sig)

    def test(self):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self.install()
        self.start()
        self.stop()
        print("TEST OK")

    @builder_method()
    def sandbox(
        self,
        reset=False,
        zhub_client=None,
        flist_create=False,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and create flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param create_flist: create flist after copying files
        :type create_flist:bool
        :param zhub_client: hub instance to upload flist tos
        :type zhub_client:str
        """
        dest_path = self.DIR_SANDBOX
        j.builders.web.openresty.sandbox(reset=reset)

        bins = ["traefik"]
        for bin_name in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin_name)
            dir_dest = self.tools.joinpaths(dest_path, j.core.dirs.BINDIR[1:])
            self.tools.dir_ensure(dir_dest)
            self._copy(dir_src, dir_dest)

        lib_dest = self.tools.joinpaths(dest_path, "sandbox/lib")
        self.tools.dir_ensure(lib_dest)
        for bin in bins:
            dir_src = self.tools.joinpaths(j.core.dirs.BINDIR, bin)
            j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)
