from Jumpscale import j


class BuilderPyFTPServer(j.baseclasses.builder):
    def install(self, root="/storage/ftpserver", config="", port=2121, reset=False):
        """
        example config
            config='''
                home:
                  guest2: ['123456']
                  root: ['1234', elradfmwM]
                public:
                  guest: ['123456']
                  anonymous: []
            '''
        key is subpath in rootpath
        then users who have access

        cannot have same user in multiple dirs (shortcoming for now, need to investigate)

        . is home dir for user

        to set specific permissions is 2e element of list


        permissions
        ```
        Read permissions:
        "e" = change directory (CWD, CDUP commands)
        "l" = list files (LIST, NLST, STAT, MLSD, MLST, SIZE commands)
        "r" = retrieve file from the server (RETR command)
        Write permissions:

        "a" = append data to an existing file (APPE command)
        "d" = delete file or directory (DELE, RMD commands)
        "f" = rename file or directory (RNFR, RNTO commands)
        "m" = create directory (MKD command)
        "w" = store a file to the server (STOR, STOU commands)
        "M" = change mode/permission (SITE CHMOD command)
        ```
        """
        if not reset and self._done_get("install"):
            return

        j.builders.system.python_pip.install("pyftpdlib")
        self.configure(root=root, config=config, port=port)

        self._done_set("install")

        self.start()

    def configure(self, root="/storage/ftpserver", config="", port=2121):
        """
        see install docstring for config example
        """
        if j.builders.platformtype.platform_is_linux:
            j.builders.system.package.ensure("btrfs-tools")
        elif j.builders.platformtype.isOSX():
            # TODO install btrfs for mac
            pass

        j.builders.storage.btrfs.subvolumeCreate(root)

        if config == "":
            authorizer = "    from pyftpdlib.authorizers import UnixAuthorizer"
        else:
            authorizer = ""
            configmodel = j.data.serializers.yaml.loads(config)
            for key, obj in configmodel.items():
                j.builders.storage.btrfs.subvolumeCreate(self._joinpaths(root, key))
                for user, obj2 in obj.items():
                    if user.lower() == "anonymous":
                        authorizer += "    authorizer.add_anonymous('%s')\n" % self._joinpaths(root, key)
                    else:
                        if len(obj2) == 1:
                            # no rights
                            rights = "elradfmwM"
                            secret = obj2[0]
                        elif len(obj2) == 2:
                            secret, rights = obj2
                        else:
                            raise j.exceptions.Input("wrong format in ftp config:%s, for user:%s" % (config, user))
                        authorizer += "    authorizer.add_user('%s', '%s', '%s', perm='%s')\n" % (
                            user,
                            secret,
                            self._joinpaths(root, key),
                            rights,
                        )

        C = """
        from pyftpdlib.authorizers import DummyAuthorizer
        from pyftpdlib.handlers import FTPHandler
        from pyftpdlib.servers import FTPServer

        def main():
            # Instantiate a dummy authorizer for managing 'virtual' users
            authorizer = DummyAuthorizer()

            # Define a new user having full r/w permissions and a read-only
            # anonymous user
        $authorizers

            # Instantiate FTP handler class
            handler = FTPHandler
            handler.authorizer = authorizer

            # Define a customized banner (string returned when client connects)
            handler.banner = "ftpd ready."

            # Specify a masquerade address and the range of ports to use for
            # passive connections.  Decomment in case you're behind a NAT.
            #handler.masquerade_address = '151.25.42.11'
            handler.passive_ports = range(60000, 65535)

            # Instantiate FTP server class and listen on 0.0.0.0:2121
            address = ('0.0.0.0', $port)
            server = FTPServer(address, handler)

            # set a limit for connections
            server.max_cons = 256
            server.max_cons_per_ip = 20

            # start ftp server
            server.serve_forever()

        if __name__ == '__main__':
            main()
        """
        C = j.core.text.strip(C)

        C = C.replace("$port", str(port))
        C = C.replace("$authorizers", authorizer)

        j.core.tools.dir_ensure("$CFGDIR/ftpserver")
        self._write("$CFGDIR/ftpserver/start.py", C)

    def start(self):
        pm = j.builders.system.processmanager.get()
        pm.ensure("pyftpserver", "python3 $CFGDIR/ftpserver/start.py")

    def stop(self):
        pm = j.builders.system.processmanager.get()
        pm.stop("pyftpserver")
