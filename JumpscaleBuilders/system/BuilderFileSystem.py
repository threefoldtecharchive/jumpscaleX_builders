import uuid
import time
from Jumpscale import j
import Jumpscale


class BuilderFileSystem(j.baseclasses.builder):
    def create(self, device, fs_type="ext4"):
        """
        Create filesystem on a data disk
        
        @fs_type (default 'ext4'): type of the new filesystem
        @device: device name (ex. /dev/vdb) 
        """
        prefab = self.prefab
        cmd = "mkfs.%s %s" % (fs_type, device)
        prefab.executor.execute(cmd)

    def mount(self, mount_point, device, copy=False, append_fstab=False, fs_type=None):
        """
        Mount file system

        @device (required): device name to mount (ex. /dev/vdb)
        @mount_point (required): mount point (ex. /var)
        @copy (default to False):  copy old data from @mount_point directory to the new device
        @append_fstab (default to False): append fstab file
        @fs_type (required only if @append_fstab==True): type of the new filesystem (ex. 'ext4')
        """

        prefab = self.prefab
        mount_point.strip().rstrip("/")

        # make sure mount point folder exists
        tools.createDir(mount_point)

        if copy:
            # generate random tmp folder name
            tmp = "/mnt/tmp%s" % str(uuid.uuid4()).replace("-", "")

            # mount new filesystem in tmp mount point
            tools.createDir(tmp)
            try:
                prefab.executor.execute("mount %s %s" % (device, tmp))
                try:
                    # backup data at the mount point in temporary directory
                    prefab.executor.execute("cp -ax %s/* %s" % (mount_point, tmp))
                finally:
                    # unmount the partition
                    prefab.executor.execute("umount %s" % device)
            finally:
                tools.dir_remove(tmp)

        # mount device
        prefab.executor.execute("mount %s %s" % (device, mount_point))

        if append_fstab:
            # check type of fs is given
            if not fs_type:
                raise j.exeptions.Input("fs_type must be given")
            # append to fstab
            tools.file_append("/etc/fstab", "%s\t%s\t%s\tdefaults\t0 0" % (device, mount_point, fs_type))
