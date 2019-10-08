from Jumpscale import j
from parameterized import parameterized
from .base_test import BaseTest


class StorageTestCases(BaseTest):
    @parameterized.expand(
        [
            ("btrfs", "btrfs"),
            ("duplicacy", "duplicacy"),
            ("fuse", "fuse"),
            ("ipfs", "ipfs"),
            ("minio", "minio"),
            ("syncthing", "syncthing"),
            ("s3scality", "s3scality"),
            ("stor", "stor"),
            ("zflist", "zflist"),
            ("zstor", "zdb"),
        ]
    )
    def test001_storage_builders(self, builder, process):
        """ BLD-001
        *Test db builers*
        """
        skipped_builders = {
            "btrfs": "https://github.com/threefoldtech/jumpscaleX_builders/issues/20",
            "duplicacy": "https://github.com/threefoldtech/jumpscaleX_builders/issues/19",
            "fuse": "https://github.com/threefoldtech/jumpscaleX_builders/issues/21",
            "stor": "https://github.com/threefoldtech/jumpscaleX_builders/issues/22",
        }
        if builder in skipped_builders:
            self.skipTest(skipped_builders[builder])
        self.info(" * {} builder: run build method.".format(builder))
        getattr(j.builders.storage, builder).build()
        self.info(" * {} builder: run install  method.".format(builder))
        getattr(j.builders.storage, builder).install()
        self.info(" * {} builder: run start method.".format(builder))
        try:
            getattr(j.builders.storage, builder).start()
        except RuntimeError as e:
            self.fail(e)
        self.info(" * check that {} server started successfully.".format(builder))
        self.small_sleep()
        self.assertTrue(len(j.sal.process.getProcessPid(process)))
        self.info(" * {} builder: run stop method.".format(builder))
        try:
            getattr(j.builders.storages, builder).stop()
        except RuntimeError as e:
            self.fail(e)
        self.info(" *  check that {} server stopped successfully.".format(builder))
        self.small_sleep()
        self.assertFalse(len(j.sal.process.getProcessPid(process)))

    def test002_restic(self):
        """ BLD-033
        *Test restic builer*
        """
        self.info(" * restic builder: run build method.")
        j.builders.storage.restic.build(reset=True)
        self.info(" * restic builder: run install method.")
        j.builders.storage.restic.install()
        try:
            self.info(" * check that libffi is installed successfully")
            j.sal.process.execute("which restic")
        except:
            self.assertTrue(False)
