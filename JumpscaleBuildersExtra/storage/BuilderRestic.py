from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


class BuilderRestic(BuilderGolangTools):

    __jslocation__ = "j.builders.storage.restic"

    def _init(self, **kwargs):
        super()._init()

        # self.env = self.bash.profile

        self.DIR_CLONE = "{DIR_CODE}/github/restic"
        self.DIR_RESTIC = self._replace("{DIR_CLONE}/restic")
        self.DIR_REST = self._replace("{DIR_CLONE}/rest-server")

        self._dir_ensure(self.DIR_CLONE)

    @builder_method()
    def build(self, reset=False):

        # install golang dependancy
        if not j.sal.fs.exists("{DIR_BIN}/go"):
            j.builders.runtimes.go.install(reset=True)

        cmd = self._replace(
            """
            cd {DIR_CLONE}
            rm -rf restic/
            git clone --depth 1 https://github.com/restic/restic.git
        """
        )
        self._execute(cmd, timeout=1200)

        cmd = self._replace(
            """
            cd {DIR_CLONE}
            rm -rf rest-server/
            git clone --depth 1 https://github.com/restic/rest-server.git
        """
        )
        self._execute(cmd, timeout=1200)

        self.profile.env_set("GO111MODULE", "on")

        # build binaries
        build_cmd = self._replace("cd {DIR_RESTIC}; go run -mod=vendor build.go -k -v")
        self._execute(build_cmd, timeout=1000)

        build_cmd = self._replace("cd {DIR_REST}; go run build.go")
        self._execute(build_cmd, timeout=1000)

    @builder_method()
    def install(self):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        self._copy("{DIR_RESTIC}/restic", "{DIR_BIN}")
        self._copy("{DIR_REST}/rest-server", "{DIR_BIN}")

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
        :type create_flist:bool
        :param zhub_instance: hub instance to upload flist to
        :type zhub_instance:str
        """

        dest_path = self.DIR_SANDBOX
        dir_src = self._joinpaths(j.core.dirs.BINDIR, "restic")
        dir_dest = self._joinpaths(dest_path, j.core.dirs.BINDIR[1:])
        self._dir_ensure(dir_dest)
        self._copy(dir_src, dir_dest)
        lib_dest = self._joinpaths(dest_path, "sandbox/lib")
        self._dir_ensure(lib_dest)
        j.tools.sandboxer.libs_sandbox(dir_src, lib_dest, exclude_sys_libs=False)

    @builder_method()
    def clean(self):
        self._remove(self.DIR_RESTIC)
        self._remove(self.DIR_REST)

    @builder_method()
    def reset(self):
        super().reset()
        self.clean()

    @builder_method()
    def test(self):
        return_code, _, _ = self._execute("restic version")
        assert return_code == 0
        print("TEST OK")


# class ResticRepository:
#     '''This class represent a restic repository used for backup'''

#     def __init__(self, path, password, prefab, repo_env=None):
#         self.path = path
#         self.__password = password
#         self.repo_env = repo_env
#         self.prefab = prefab

#         if not self._exists():
#             self.initRepository()

#     def _exists(self):
#         rc, _, _ = self._run('{DIR_BIN}/restic snapshots > /dev/null', die=False)
#         if rc > 0:
#             return False
#         return True

#     def _run(self, cmd, env=None, die=True, showout=True):
#         env_vars = {
#             'RESTIC_REPOSITORY': self.path,
#             'RESTIC_PASSWORD': self.__password
#         }
#         if self.repo_env:
#             env_vars.update(self.repo_env)
#         if env:
#             env_vars.update(env)
#         return j.sal.process.execute(cmd=cmd, env=env_vars, die=die, showout=showout)

#     def initRepository(self):
#         '''
#         initialize the repository at self.path location
#         '''
#         cmd = '{DIR_BIN}/restic init'
#         self._run(cmd)

#     def snapshot(self, path, tag=None):
#         '''
#         @param path: directory/file to snapshot
#         @param tag: tag to add to the snapshot
#         '''
#         cmd = '{DIR_BIN}/restic backup {} '.format(path)
#         if tag:
#             cmd += ' --tag {}'.format(tag)
#         self._run(cmd)

#     def restore_snapshot(self, snapshot_id, dest):
#         '''
#         @param snapshot_id: id of the snapshot to restore
#         @param dest: path where to restore the snapshot to
#         '''
#         cmd = '{DIR_BIN}/restic restore --target {dest} {id} '.format(dest=dest, id=snapshot_id)
#         self._run(cmd)

#     def list_snapshots(self):
#         '''
#         @return: list of dict representing a snapshot
#         { 'date': '2017-01-17 16:15:28',
#           'directory': '/optvar/cfg',
#           'host': 'myhost',
#           'id': 'ec853b5d',
#           'tags': 'backup1'
#         }
#         '''
#         cmd = '{DIR_BIN}/restic snapshots'
#         _, out, _ = self._run(cmd, showout=False)

#         snapshots = []
#         for line in out.splitlines()[2:-2]:
#             ss = list(self._chunk(line))

#             snapshot = {
#                 'id': ss[0],
#                 'date': ' '.join(ss[1:3]),
#                 'host': ss[3]
#             }
#             if len(ss) == 6:
#                 snapshot['tags'] = ss[4]
#                 snapshot['directory'] = ss[5]
#             else:
#                 snapshot['tags'] = ''
#                 snapshot['directory'] = ss[4]
#             snapshots.append(snapshot)

#         return snapshots

#     def check_repo_integrity(self):
#         '''
#         @return: True if integrity is ok else False
#         '''
#         cmd = '{DIR_BIN}/restic check'
#         rc, _, _ = self._run(cmd)
#         if rc != 0:
#             return False
#         return True

#     def _chunk(self, line):
#         '''
#         passe line and yield each word separated by space
#         '''
#         word = ''
#         for c in line:
#             if c == ' ':
#                 if word:
#                     yield word
#                     word = ''
#                 continue
#             else:
#                 word += c
#         if word:
#             yield word
