from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method
import xml.etree.ElementTree as etree
import time


class BuilderSyncthing(BuilderGolangTools):

    __jslocation__ = "j.builders.storage.syncthing"

    def _init(self, **kwargs):
        super()._init()
        # isolate GOPATH, some dependences conflict with other builders
        self.DIR_GO_PATH = self._replace("{DIR_BUILD}/go_proj")
        self.package_path = self.package_path_get("syncthing", host="github.com/syncthing")

    def profile_builder_set(self):
        self.update_profile_paths(self.profile)

    @builder_method()
    def build(self, version=None):
        """
        build and setup syncthing to run on :8384 , this can be changed from the config file in /optvar/cfg/syncthing
        version e.g. 'v0.14.5'
        """
        j.builders.runtimes.go.install()
        self.get("github.com/syncthing/syncthing/...", install=False, update=True)

        if version is not None:
            self._execute("cd %s && go run build.go -version %s -no-upgrade" % (self.package_path, version))
        else:
            self._execute("cd %s && go run build.go" % self.package_path)

    @builder_method()
    def install(self, start=True, reset=False, homedir=""):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        src = "{}/bin/syncthing".format(self.package_path)
        self._copy(src, "{DIR_BIN}/startupcmd_syncthing")  # necessary to rename executable in order to run in tmux
        if not self.tools.dir_exists("{DIR_CFG}/syncthing"):
            cmd = "{DIR_BIN}/startupcmd_syncthing -generate  {DIR_CFG}/syncthing"
        else:
            cmd = "rm -rf {DIR_CFG}/syncthing; {DIR_BIN}/startupcmd_syncthing -generate  {DIR_CFG}/syncthing"

        self._execute(cmd)

        j.builders.tools.execute("useradd syncthing || true")
        j.builders.tools.execute(self._replace("chown -R syncthing:syncthing {DIR_CFG}/syncthing"))

    @builder_method()
    def sandbox(
        self,
        zhub_client=None,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
        """Copy built bins to dest_path and reate flist if create_flist = True

        :param dest_path: destination path to copy files into
        :type dest_path: str
        :param sandbox_dir: path to sandbox
        :type sandbox_dir: str
        :param reset: reset sandbox file transfer
        :type reset: bool
        :param create_flist: create flist after copying files
        :type flist_create:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """
        dest_path = self.DIR_SANDBOX
        dir_src = self._joinpaths(j.core.dirs.BINDIR, "syncthing")
        dir_dest = self._joinpaths(dest_path, j.core.dirs.BINDIR[1:])
        self._dir_ensure(dir_dest)
        self._copy(dir_src, dir_dest)
        lib_dest = self._joinpaths(dest_path, "sandbox/lib")
        self._dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    @builder_method()
    def clean(self):
        self._remove(self.package_path)
        self._remove(self.DIR_SANDBOX)

    @builder_method()
    def stop(self):
        # stop syncthing
        j.sal.process.killProcessByName(self._name)

    @property
    def startup_cmds(self):
        cmd = self._replace("sudo -u syncthing {DIR_BIN}/startupcmd_syncthing -home  {DIR_CFG}/syncthing")
        cmds = [j.servers.startupcmd.get(name=self._name, cmd_start=cmd)]
        return cmds

    @builder_method()
    def test(self):
        # trying to get syncthing id from api and compare it with the one in config files
        if self.running():
            self.stop()

        self.start()
        time.sleep(3)
        sync_client = j.clients.syncthing.get("test", port=8384, addr="localhost", apikey=self.apikey)
        status = sync_client.status_get()
        device_id = status["myID"]
        assert device_id == self.myid
        self.stop()

        print("TEST OK")

    @property
    def apikey(self):
        tree = etree.parse(self._replace("{DIR_CFG}/syncthing/config.xml"))
        root = tree.getroot()
        gui = root.find("gui")
        apikey = gui.find("apikey")
        return apikey.text

    @property
    def myid(self):
        tree = etree.parse(self._replace("{DIR_CFG}/syncthing/config.xml"))
        root = tree.getroot()
        device = root.find("device")
        device_id = device.get("id")
        return device_id
