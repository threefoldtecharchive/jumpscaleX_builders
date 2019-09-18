import unittest
from Jumpscale import j
from .base_test import BaseTest
from parameterized import parameterized


class Storage_TestCases(BaseTest):
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
            ("zstor", "zdb")
        ]
    )
    def test_storage_flists(self, flist, binary):
        """ SAN-009
        *Test storage builers sandbox*
        """
        skipped_flists = {
            "btrfs": "not done yet",
            "duplicacy": "not done yet",
            "fuse": "not done yet",
            "stor": "not done yet",
            "zflist": "not done yet"
        }
        if flist in skipped_flists:
            self.skipTest(skipped_flists[flist])
        self.info("run {} sandbox.".format(flist))
        getattr(j.builders.storage, flist).sandbox(**self.sandbox_args)
        self.info("Deploy container with uploaded {} flist.".format(flist))
        self.deploy_flist_container("{}".format(flist))
        self.info("Check that {} flist works.".format(flist))
        if flist == "minio":
            self.assertIn("USAGE:", self.check_container_flist("/sandbox/bin/minio --help"))
        else:
            self.assertIn("Usage", self.check_container_flist("/sandbox/bin/{} help".format(binary)))
