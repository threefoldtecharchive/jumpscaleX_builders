import os
from Jumpscale import j


class BuilderSmartmontools(j.baseclasses.builder):
    """
    Builder module for smartmontools (smartctl command)
    """

    __jslocation__ = "j.builders.monitoring.smartmontools"

    _DOWNLOAD_URL = "http:/builds.smartmontools.org/r4592/smartmontools-6.6-0-20171104-r4592.linux-x86_64-static.tar.gz"
    _VERSION = "6.6"
    _REL_INSTALL_LOCATION = j.sal.fs.joinPaths("usr", "local", "sbin")

    def install(self):
        """
        Installs version 6.6 of smartmontools
        (apt-get version is 6.5
        Version 6.6 is needed for NVMe support)
        Ensures smartctl is installed
        """
        if self.isInstalled():
            self._log_info("smartctl version %s is present" % self._VERSION)
            return

        self._log_info("installing smartctl...")

        tmp_location = j.builders.tools.file_download(self._DOWNLOAD_URL, expand=True)

        # move downloaded binary to installation destination
        self._execute(
            "mv %s %s"
            % (
                j.sal.fs.joinPaths(tmp_location, self._REL_INSTALL_LOCATION, "smartctl"),
                j.sal.fs.joinPaths(os.sep, self._REL_INSTALL_LOCATION),
            )
        )

        # cleanup
        j.builders.tools.dir_remove(tmp_location)

        if not self.isInstalled():
            raise j.exceptions.Base("Failed to install Smartmontools")

    def isInstalled(self):
        """
        Checks smartctl of the correct version is installed
        """
        # check if command exists with a version call
        cmd = "smartctl --version"
        rc, out, err = j.sal.process.execute(cmd, die=False)
        if rc != 0:
            self._log_warning("'smartctl --version' failed, assuming it's not installed: %s", err)
            return False

        # version number should be the second word of the first line
        version = out.split()[1]
        self._log_debug("smartctl version '%s' found" % version)

        if version != self._VERSION:
            self._log_warning(
                "smartctl found but was version: %s\nNeed version %s to be installed" % (version, self._VERSION)
            )
            return False

        return True
