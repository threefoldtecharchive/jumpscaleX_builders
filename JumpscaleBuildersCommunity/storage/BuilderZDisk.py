import os.path
from Jumpscale import j


_NBDSERVER_CONFIG_FILE = "{DIR_BASE}/config/nbdserver/config.yaml"
_DEFAULT_LOCAL_CONFIG_FILE = "./config.yaml"


class BuilderZDisk(j.builders.system._BaseClass):
    """
    Manages 0-Disk over prefab
    """

    NAME = "0-disk"

    def build(self, branch="master", reset=False):
        """
        Download and builds 0-disk on the prefab machine
        :param reset: reinstalls if reset is True
        :return:
        """
        if self.is_installed() and not reset:
            self._log_info("0-Disk was already installed, pass reset=True to reinstall.")
            return

        # install dependencies
        j.builders.system.package.ensure("git")
        j.builders.runtimes.golang.install()

        # install 0-Disk
        install_path = j.sal.fs.joinPaths(j.builders.runtimes.golang.GOPATH, "src", "github.com", "zero-os")
        j.core.tools.dir_ensure(install_path)
        cmd = """
        cd {0}
        rm -rf ./0-Disk
        git clone -b {1} https://github.com/zero-os/0-Disk.git

        cd ./0-Disk
        make

        cp -a bin/. {DIR_BIN}
        """.format(
            install_path, branch
        )

        cmd = self._replace(cmd)

        j.sal.process.execute(cmd)

    def install(self, branch="master", reset=False):
        """
        Installs 0-disk
        Alias for build
        :param reset: reinstall if reset is True
        :return:
        """
        return self.build(branch=branch, reset=reset)

    def is_installed(self):
        """Returns True if 0-Disk is installed"""

        return (
            j.builders.tools.command_check("nbdserver")
            and j.builders.tools.command_check("tlogserver")
            and j.builders.tools.command_check("zeroctl")
        )

    def start_nbdserver(
        self,
        address=None,
        config_file=None,
        config_cluster=None,
        id=None,
        lbacachelimit=None,
        logfile=None,
        profile_address=None,
        protocol=None,
        tlog_priv_key=None,
        tlsonly="false",
    ):
        """
        Starts the 0-disk\'s nbdserver
        Check the 0-Disk documentation for details of the flags
        (https://github.com/zero-os/0-Disk/blob/master/docs/nbd/using.md)

        The config flag is split into 2 variables:
        With config_file the config file will be uploaded to the nbd's machine
        With config_cluster the etcd clusted used for config can be passed
        Only one of these parameters can be set
        """
        if config_file is not None and config_cluster is not None:
            raise j.exceptions.Value("Both config_file and config_file parameters were provided")

        config = ""
        if config_cluster is not None:
            config = config_cluster
        else:
            if config_file is None:
                config_file = _DEFAULT_LOCAL_CONFIG_FILE
            if not os.path.isfile(config_file):
                raise j.exceptions.Value("Could not find local config file: {}".format(config_file))
            j.builders.tools.upload(config_file, _NBDSERVER_CONFIG_FILE)
            # set config to file location
            j.builders.tools.file_ensure(_NBDSERVER_CONFIG_FILE)
            config = _NBDSERVER_CONFIG_FILE
            pass

        j.builders.system.process.kill("nbdserver")

        # assemble command
        cmd = "nbdserver"

        if address is not None:
            cmd += " --address {}".format(address)
        if config != "":
            cmd += " --config {}".format(config)
        if id is not None:
            cmd += " --id {}".format(id)
        if lbacachelimit is not None:
            cmd += " --lbacachelimit {}".format(lbacachelimit)
        if logfile is not None:
            cmd += " --logfile {}".format(logfile)
        if profile_address is not None:
            cmd += " --profile-address {}".format(profile_address)
        if protocol is not None:
            cmd += " --protocol {}".format(protocol)
        if tlog_priv_key is not None:
            cmd += " --tlog-priv-key {}".format(tlog_priv_key)
        if tlsonly is not None:
            cmd += " --tlsonly {}".format(tlsonly)

        cmd = self._replace(cmd)

        j.sal.process.execute(cmd)

    def start_tlogserver(self, config):
        """Starts the 0-disk\'s tlogserver"""
        raise j.exceptions.NotImplemented

    def stop_nbdserver(self):
        """Stops the 0-disk\'s nbdserver"""
        pm = j.builders.system.processmanager.get()
        pm.stop("nbdserver")

    def stop_tlogserver(self):
        """Stops the 0-disk\'s tlogserver"""
        raise j.exceptions.NotImplemented
