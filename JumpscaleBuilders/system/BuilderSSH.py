from grp import getgrgid
from Jumpscale import j
import netaddr


class BuilderSSH(j.baseclasses.builder):

    # def test_login(self, passwd, port=22, ip_range=None, onlyplatform='arch'):
    #     login = 'root'
    #     res = []
    #     for item in self.scan(ip_range=ip_range):
    #         self._log_info('test for login/passwd on %s' % item)
    #         try:
    #             client = j.clients.ssh.new(addr=item, port=port, login=login, passwd=passwd, timeout=1, die=False)
    #         except Exception as e:
    #             self._log_info('  NOT OK')
    #             continue
    #         executor = j.tools.executor.getSSHBased(item, port, login, passwd, checkok=True)
    #         if onlyplatform:
    #             if not str(executor.prefab.platformtype).startswith(onlyplatform):
    #                 continue
    #         self._log_info('  RESPONDED!!!')
    #         res.append(item)
    #     return res

    # def test_login_pushkey(self, passwd, keyname, port=22, range=None, changepasswdto='', onlyplatform='arch'):
    #     """
    #     """
    #     login = 'root'
    #     done = []
    #     for item in self.test_login(passwd, port, range, onlyplatform=onlyplatform):
    #         keypath = j.sal.fs.joinPaths(j.core.myenv.config[''], '.ssh', keyname + '.pub')
    #         if j.sal.fs.exists(keypath):
    #             key = j.sal.fs.readFile(keypath)
    #             executor = j.tools.executor.getSSHBased(item, port, login, passwd, checkok=True)
    #             executor.prefab.system.ssh.authorize(user='root', key=key)
    #             if changepasswdto != '':
    #                 executor.prefab.system.user.passwd(login, changepasswdto, encrypted_passwd=False)
    #         else:
    #             raise j.exceptions.RuntimeError('Cannot find key:%s' % keypath)
    #         done.append(item)
    #     return done

    def scan(self, ip_range=None, ips={}, port=22):
        """Scan hosts

        :param range: range in format 192.168.0.0/24, defaults to None
        :type range: str, optional
        :param ips: ips to macaddress mapping, defaults to {}
        :type ips: dict, optional
        :param port: port number to use for scanning, defaults to 22
        :type port: int, optional
        :return: ips to macaddress mapping
        :rtype: dict
        """
        if not ip_range:
            res = j.builders.system.net.get_info()
            for item in res:
                cidr = item["cidr"]

                name = item["name"]
                if not name.startswith("docker") and name not in ["lo"]:
                    if len(item["ip"]) > 0:
                        ip = item["ip"][0]
                        ipn = netaddr.IPNetwork(ip + "/" + str(cidr))
                        ip_range = str(ipn.network) + "/%s" % cidr
                        ips = self.scan(ip_range, ips)
            return ips
        else:
            try:
                # out=j.sal.process.execute('nmap -p 22 %s | grep for'%range,showout=False)
                _, out, _ = j.sal.process.execute("nmap %s -p %s --open -oX {DIR_TEMP}/nmap" % (ip_range, port))
            except Exception as e:
                if str(e).find("command not found") != -1:
                    j.builders.system.package.ensure("nmap")
                    # out=j.sal.process.execute('nmap -p 22 %s | grep for'%range)
                    _, out, _ = j.sal.process.execute("nmap %s -p %s --open -oX {DIR_TEMP}/nmap" % (ip_range, port))
            out = j.core.tools.file_text_read("{DIR_TEMP}/nmap")
            import xml.etree.ElementTree as ET

            root = ET.fromstring(out)
            for child in root:
                if child.tag == "host":
                    ip = None
                    mac = None
                    for addr in child.findall("address"):
                        if addr.get("addrtype") == "ipv4":
                            ip = addr.get("addr")

                    for addr in child.findall("address"):
                        if addr.get("addrtype") == "mac":
                            mac = addr.get("addr")

                    if ip is not None:
                        ips[ip] = {"mac": mac}

            # for line in out.split('\n'):
            #     ip=line.split('for')[1].strip()
            #     if ip.find('(')!=-1:
            #         ip=ip.split('(')[1].strip(')').strip()
            #     if ip not in ips:

            #         ips.append(ip)
            return ips

    def define_host(self, addr, user="root", port=22):
        """Add a host to know_hosts of a certain user

        :param addr: host address
        :type addr: str
        :param user: user name, defaults to 'root'
        :type user: str, optional
        :param port: host port, defaults to 22
        :type port: int, optional
        """
        known_hostsfile = "/{}/.ssh/known_hosts".format(user)
        lines = j.core.tools.file_text_read(known_hostsfile, default="").splitlines()
        isknown = False
        for line in lines:
            if line.startswith(addr):
                isknown = True
                break
        if not isknown:
            j.sal.process.execute("ssh-keyscan -p {} -t rsa {} >> {}".format(port, addr, known_hostsfile))

    def keygen(self, user="root", keytype="rsa", name="default"):
        """
        Generates a pair of ssh keys in the user's home .ssh directory

        :param user: username, defaults to 'root'
        :type user: str, optional
        :param keytype: type of the key, defaults to 'rsa'
        :type keytype: str, optional
        :param name: key name, defaults to 'default'
        :type name: str, optional
        :return: generated key path
        :rtype: str
        """
        user = user.strip()
        d = j.builders.system.user.check(user)
        assert d, "User does not exist: %s" % (user)
        home = d["home"]
        path = "%s/.ssh/%s" % (home, name)
        if not j.builders.tools.file_exists(path + ".pub"):
            j.core.tools.dir_ensure(home + "/.ssh", mode="0700", owner=user, group=user)

            j.sal.process.execute("ssh-keygen -q -t %s -f %s -N ''" % (keytype, path))
            j.builders.tools.file_attribs(path, mode="0600", owner=user, group=user)
            j.builders.tools.file_attribs("%s.pub" % path, mode="0600", owner=user, group=user)
            return "%s.pub" % path
        else:
            return "%s.pub" % path

    def authorize(self, user, key, **kwargs):
        """Adds the given key to the '.ssh/authorized_keys' for the given
        user.

        kwargs are used for extra settings for this authorization. See https://www.ssh.com/ssh/authorized_keys/openssh
        E.g. setting command option is done by adding the following kwarg: command=''/bin/myscript.sh'
        E.g. setting no-agent-forwarding is done by adding the following kwarg: no-agent-forwarding=True


        :param user: username to which authorization should be performed
        :type user: str
        :param key: public ssh key to authorize
        :type key: str
        :raises j.exceptions.Input: if the key is empty
        :raises j.exceptions.RuntimeError: if user is not found
        :return: True if the key already exists, False otherwise
        :rtype: bool
        """

        def add_newline(content):
            if content and content[-1] != "\n":
                content += "\n"
            return content

        if key is None or key.strip() == "":
            raise j.exceptions.Input("key cannot be empty")
        user = user.strip()
        d = j.builders.system.user.check(user, need_passwd=False)
        if d is None:
            raise j.exceptions.RuntimeError("did not find user:%s" % user)
        # group = getgrgid(d['gid']).gr_name #GAVE THE WRONG ANSWER, THINK WE CAN PUT ON ROOT BY DEFAULT
        group = "root"
        keyf = d["home"] + "/.ssh/authorized_keys"
        key = add_newline(key)
        ret = None

        settings = list()
        for setting, value in kwargs.items():
            if value is True:
                settings.append(setting)
            else:
                settings.append('%s="%s"' % (setting, value))
        if settings:
            line = "%s %s" % (",".join(settings), key)
        else:
            line = key

        if j.builders.tools.file_exists(keyf):
            content = j.core.tools.file_text_read(keyf)
            if content.find(key[:-1]) == -1:
                content = add_newline(content)
                self._write(keyf, content + line)
                ret = False
            else:
                ret = True
        else:
            # Make sure that .ssh directory exists, see #42
            j.core.tools.dir_ensure(j.sal.fs.getDirName(keyf))
            self._write(keyf, line)
            j.sal.fs.chown(keyf, user, group)
            j.sal.fs.chmod(keyf, 600)
            ret = False

        return ret

    def unauthorize(self, user, key):
        """Removes the given key from the remote '.ssh/authorized_keys' for the given
        user

        :param user: the user to remove the key from
        :type user: str
        :param key: the key to remove
        :type key: str
        :return: True if successfully removed, False otherwise
        :rtype: bool
        """
        key = key.strip()
        d = j.builders.system.user.check(user, need_passwd=False)
        group = d["gid"]
        keyf = d["home"] + "/.ssh/authorized_keys"
        if j.builders.tools.file_exists(keyf):
            self._write(
                keyf,
                "\n".join(_ for _ in j.core.tools.file_text_read(keyf).split("\n") if _.strip() != key),
                owner=user,
                group=group,
                mode="600",
            )
            return True
        else:
            return False

    def unauthorizeAll(self):
        """
        Removes all keys and known hosts
        """
        self._log_info("clean known hosts/autorized keys")
        j.core.tools.dir_ensure("%s/.ssh" % j.core.myenv.config["DIR_HOME"])
        self._remove("%s/.ssh/known_hosts" % j.core.myenv.config["DIR_HOME"])
        self._remove("%s/.ssh/authorized_keys" % j.core.myenv.config["DIR_HOME"])

    def enableAccess(self, keys, backdoorpasswd, backdoorlogin="backdoor", user="root"):
        """Enable access for a list of keys

        :param keys: a list of ssh pub keys
        :type keys: list
        :param backdoorpasswd: backdoor password
        :type backdoorpasswd: str
        :param backdoorlogin: backdoor login, defaults to 'backdoor'
        :type backdoorlogin: str, optional
        :param user: the user to ensure exists, defaults to 'root'
        :type user: str, optional
        :raises j.exceptions.RuntimeError: raises an error if any of the keys are empty
        """
        # leave here is to make sure we have a backdoor for when something goes wrong further
        self._log_info("create backdoor")
        j.builders.system.user.ensure(
            backdoorlogin,
            passwd=backdoorpasswd,
            home=None,
            uid=None,
            gid=None,
            shell=None,
            fullname=None,
            encrypted_passwd=True,
            group="root",
        )
        j.sal.process.execute("rm -fr /home/%s/.ssh/" % backdoorlogin)
        j.builders.system.group.user_add("sudo", "$(system.backdoor.login)")

        self._log_info("test backdoor")
        j.tools.executor.getSSHBased(
            addr="$(node.tcp.addr)",
            port=int("$(ssh.port)"),
            login="$(system.backdoor.login)",
            passwd=backdoorpasswd,
            debug=False,
            checkok=True,
            allow_agent=False,
            look_for_keys=False,
        )
        # make sure the backdoor is working
        self._log_info("backdoor is working (with passwd)")

        self._log_info("make sure some required packages are installed")
        j.builders.system.package.ensure("openssl")
        j.builders.system.package.ensure("rsync")

        self.unauthorizeAll()

        for pub in keys:
            if pub.strip() == "":
                raise j.exceptions.RuntimeError("ssh.key.public cannot be empty")
            self.authorize("root", pub)

        self._log_info("add git repos to known hosts")
        j.sal.process.execute("ssh-keyscan github.com >> %s/.ssh/known_hosts" % j.core.myenv.config["DIR_HOME"])
        j.sal.process.execute("ssh-keyscan git.aydo.com >> %s/.ssh/known_hosts" % j.core.myenv.config["DIR_HOME"])

        self._log_info("enable access done.")

    def sshagent_add(self, path, removeFirst=True):
        """Add key to ssh agent

        :param path: path to private key
        :type path: str
        :param removeFirst: remove it first from ssh agent, defaults to True
        :type removeFirst: bool, optional
        :raises j.exceptions.RuntimeError: raises runtime error if it fails to remove it first
        """
        self._log_info("add ssh key to ssh-agent: %s" % path)
        if removeFirst:
            j.sal.process.execute('ssh-add -d "%s"' % path, die=False, showout=False)
            _, keys, _ = j.sal.process.execute("ssh-add -l", die=False, showout=False)
            if path in keys:
                raise j.exceptions.RuntimeError("ssh-key is still loaded in ssh-agent, please remove manually")
        j.sal.process.execute('ssh-add "%s"' % path, showout=False)

    def sshagent_remove(self, path):
        """Remove key from ssh agent

        :param path: path to private key
        :type path: str
        :raises j.exceptions.RuntimeError: raises runtime error if it fails to remove it
        """
        self._log_info("remove ssh key to ssh-agent: %s" % path)
        j.sal.process.execute('ssh-add -d "%s"' % path, die=False, showout=False)
        _, keys, _ = j.sal.process.execute("ssh-add -l", showout=False)
        if path in keys:
            raise j.exceptions.RuntimeError("ssh-key is still loaded in ssh-agent, please remove manually")
