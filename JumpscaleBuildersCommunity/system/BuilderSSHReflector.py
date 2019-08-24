from Jumpscale import j
import os
import time

import socket


class BuilderSSHReflector(j.builders.system._BaseClass):
    def __init__(self, executor, prefab):
        self.executor = executor
        self.prefab = prefab

    def server(self, reset=False, keyname="reflector"):
        """
        configurs the server
        to test
        js 'c=j.tools.prefab.get("stor1:9022");c.installer.sshreflector.server'
        """

        port = 9222

        package = "dropbear"
        j.builders.system.package.ensure(package)

        j.sal.process.execute("rm -f /etc/default/dropbear", die=False)
        j.sal.process.execute("killall dropbear", die=False)

        passwd = j.data.idgenerator.generateGUID()
        j.builders.user.ensure(
            "sshreflector",
            passwd=passwd,
            home="/home/sshreflector",
            uid=None,
            gid=None,
            shell=None,
            fullname=None,
            encrypted_passwd=True,
            group=None,
        )

        j.sal.process.execute("ufw allow %s" % port, die=False)

        j.core.tools.dir_ensure(
            "/home/sshreflector/.ssh", recursive=True, mode=None, owner="sshreflector", group="sshreflector"
        )

        lpath = os.environ["HOME"] + "/.ssh/reflector"
        path = "/home/sshreflector/.ssh/reflector"
        ftp = j.builders.tools.executor.sshclient.sftp
        if j.sal.fs.exists(lpath) and j.sal.fs.exists(lpath + ".pub"):
            self._log_info("UPLOAD EXISTING SSH KEYS")
            ftp.put(lpath, path)
            ftp.put(lpath + ".pub", path + ".pub")
        else:
            # we do the generation of the keys on the server
            if reset or not j.builders.tools.file_exists(path) or not j.builders.tools.file_exists(path + ".pub"):
                j.builders.tools.file_unlink(path)
                j.builders.tools.file_unlink(path + ".pub")
                # -N is passphrase
                j.sal.process.execute("ssh-keygen -q -t rsa -b 4096 -f %s -N '' " % path)
            ftp.get(path, lpath)
            ftp.get(path + ".pub", lpath + ".pub")

            j.sal.fs.chmod(lpath, 0o600)
            j.sal.fs.chmod(lpath + ".pub", 0o600)

        # authorize remote server to accept now copied private key
        j.builders.system.ssh.authorize("sshreflector", j.sal.fs.readFile(lpath + ".pub"))

        j.sal.process.execute("chmod 0644 /home/sshreflector/.ssh/*")
        j.sal.process.execute("chown -R sshreflector:sshreflector /home/sshreflector/.ssh/")

        _, cpath, _ = j.sal.process.execute("which dropbear")

        cmd = "%s -R -F -E -p 9222 -w -s -g -K 20 -I 60" % cpath
        # j.builders.system.processmanager.e
        pm = j.builders.system.processmanager.get()
        pm.ensure("reflector", cmd)

        # j.builders.system.package.start(package)

        j.builders.system.ns.hostfile_set_fromlocal()

        if j.builders.system.process.tcpport_check(port, "dropbear") is False:
            raise j.exceptions.RuntimeError("Could not install dropbear, port %s was not running" % port)

    #
    def client_delete(self):
        j.builders.system.processmanager.remove("autossh")  # make sure leftovers are gone
        j.sal.process.execute("killall autossh", die=False, showout=False)

    def client(self, remoteids, reset=True):
        """
        chose a port for remote server which we will reflect to
        @param remoteids :  ovh4,ovh5:2222

        to test
        js 'c=j.tools.prefab.get("192.168.0.149");c.installer.sshreflector_client("ovh4,ovh5:2222")'

        """

        if remoteids.find(",") != -1:
            for item in remoteids.split(","):
                j.builders.sshreflector.client(item.strip())
        else:

            self.client_delete()

            j.builders.system.ns.hostfile_set_fromlocal()

            remoteprefab = j.tools.prefab.get(remoteids)

            package = "autossh"
            j.builders.system.package.ensure(package)

            lpath = os.environ["HOME"] + "/.ssh/reflector"

            if reset or not j.sal.fs.exists(lpath) or not j.sal.fs.exists(lpath_pub):
                self._log_info("DOWNLOAD SSH KEYS")
                # get private key from reflector
                ftp = remotetools.executor.sshclient.sftp
                path = "/home/sshreflector/.ssh/reflector"
                ftp.get(path, lpath)
                ftp.get(path + ".pub", lpath + ".pub")
                ftp.close()

            # upload to reflector client
            ftp = j.builders.tools.executor.sshclient.sftp
            rpath = "/root/.ssh/reflector"
            ftp.put(lpath, rpath)
            ftp.put(lpath + ".pub", rpath + ".pub")
            j.sal.process.execute("chmod 0600 /root/.ssh/reflector")
            j.sal.process.execute("chmod 0600 /root/.ssh/reflector.pub")

            if remotetools.executor.addr.find(".") != -1:
                # is real ipaddress, will put in hostfile as reflector
                addr = remotetools.executor.addr
            else:
                a = socket.gethostbyaddr(remotetools.executor.addr)
                addr = a[2][0]

            port = remotetools.executor.port

            # test if we can reach the port
            if j.sal.nettools.tcpPortConnectionTest(addr, port) is False:
                raise j.exceptions.RuntimeError("Cannot not connect to %s:%s" % (addr, port))

            rname = "refl_%s" % remotetools.executor.addr.replace(".", "_")
            rname_short = remotetools.executor.addr.replace(".", "_")

            j.builders.system.ns.hostfile_set(rname, addr)

            if remotetools.file_exists("/home/sshreflector/reflectorclients") is False:
                self._log_info("reflectorclientsfile does not exist")
                remotetools.file_write(
                    "/home/sshreflector/reflectorclients", "%s:%s\n" % (j.builders.platformtype.hostname, 9800)
                )
                newport = 9800
                out2 = remotetools.file_read("/home/sshreflector/reflectorclients")
            else:
                remotetools.file_read("/home/sshreflector/reflectorclients")
                out = remotetools.file_read("/home/sshreflector/reflectorclients")
                out2 = ""
                newport = 0
                highestport = 0
                for line in out.split("\n"):
                    if line.strip() == "":
                        continue
                    if line.find(j.builders.platformtype.hostname) != -1:
                        newport = int(line.split(":")[1])
                        continue
                    foundport = int(line.split(":")[1])
                    if foundport > highestport:
                        highestport = foundport
                    out2 += "%s\n" % line
                if newport == 0:
                    newport = highestport + 1
                out2 += "%s:%s\n" % (j.builders.platformtype.hostname, newport)
                remotetools.file_write("/home/sshreflector/reflectorclients", out2)

            j.sal.fs.writeFile("/etc/reflectorclients", out2)

            reflport = "9222"

            self._log_info("check ssh connection to reflector")
            j.sal.process.execute(
                "ssh -i /root/.ssh/reflector -o StrictHostKeyChecking=no sshreflector@%s -p %s 'ls /'"
                % (rname, reflport)
            )
            self._log_info("OK")

            _, cpath, _ = j.sal.process.execute("which autossh")
            cmd = (
                '%s -M 0 -N -o ExitOnForwardFailure=yes -o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" -R %s:localhost:22 sshreflector@%s -p %s -i /root/.ssh/reflector'
                % (cpath, newport, rname, reflport)
            )

            pm = j.builders.system.processmanager.get()
            pm.ensure("autossh_%s" % rname_short, cmd, descr="")

            self._log_info("On %s:%s remote SSH port:%s" % (remotetools.executor.addr, port, newport))

    def createconnection(self, remoteids):
        """
        @param remoteids are the id's of the reflectors e.g. 'ovh3,ovh5:3333'
        """
        j.sal.process.execute("killall autossh", die=False)
        j.builders.system.package.ensure("autossh")

        if remoteids.find(",") != -1:
            prefab = None
            for item in remoteids.split(","):
                try:
                    prefab = j.tools.prefab.get(item)
                except BaseException:
                    pass
        else:
            prefab = j.tools.prefab.get(remoteids)
        if prefab is None:
            raise j.exceptions.RuntimeError("could not find reflector active")

        rpath = "/home/sshreflector/reflectorclients"
        lpath = os.environ["HOME"] + "/.ssh/reflectorclients"
        ftp = tools.executor.sshclient.sftp
        ftp.get(rpath, lpath)

        out = j.core.tools.file_text_read(lpath)

        addr = tools.executor.addr

        keypath = os.environ["HOME"] + "/.ssh/reflector"

        for line in out.split("\n"):
            if line.strip() == "":
                continue
            name, port = line.split(":")

            # cmd="ssh sshreflector@%s -o StrictHostKeyChecking=no -p 9222 -i %s -L %s:localhost:%s"%(addr,keypath,port,port)
            # j.builders.tmux.executeInScreen("ssh",name,cmd)

            cmd = (
                'autossh -M 0 -N -f -o ExitOnForwardFailure=yes -o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" -L %s:localhost:%s sshreflector@%s -p 9222 -i %s'
                % (port, port, addr, keypath)
            )
            j.sal.process.execute(cmd)

        self._log_info("\n\n\n")
        self._log_info("Reflector:%s" % addr)
        self._log_info(out)

    def __str__(self):
        return "prefab.reflector:%s:%s" % (getattr(self.executor, "addr", "local"), getattr(self.executor, "port", ""))

    __repr__ = __str__
