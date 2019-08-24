from Jumpscale import j


class BuilderUFW(j.builders.system._BaseClass):
    def _init(self, **kwargs):
        self._ufw_allow = {}
        self._ufw_deny = {}
        self._ufw_enabled = None

    @property
    def ufw_enabled(self):
        if j.core.platformtype.myplatform.platform_is_osx:
            return False
        if not self._ufw_enabled:
            if not j.core.platformtype.myplatform.platform_is_osx:
                if self.tools.command_check("nft") is not False:
                    self._ufw_enabled = False
                    self._log_info("cannot use ufw, nft installed")
                if self.tools.command_check("ufw") is False:
                    j.builders.system.package.ensure("ufw")
                    self.tools.command_check("ufw")
                self._ufw_enabled = "inactive" not in j.sal.process.execute("ufw status")[1]
        return self._ufw_enabled

    def ufw_enable(self):
        if not self.ufw_enabled:
            if not j.core.platformtype.myplatform.platform_is_osx:
                if self.tools.command_check("nft", die=False) is not False:
                    self._fw_enabled = False
                    raise j.exceptions.RuntimeError("Cannot use ufw, nft installed")
                if self.executor.type != "local":
                    j.sal.process.execute("ufw allow %s" % self.executor.port)
                j.sal.process.execute('echo "y" | ufw enable')
                self._fw_enabled = True
                return True
            raise j.exceptions.Input(
                message="cannot enable ufw, not supported or ", level=1, source="", tags="", msgpub=""
            )
        return True

    @property
    def ufw_rules_allow(self):
        if self.ufw_enabled == False:
            return {}
        if self._ufw_allow == {}:
            self._ufw_status()
        return self._ufw_allow

    @property
    def ufw_rules_deny(self):
        if self.ufw_enabled == False:
            return {}
        if self._ufw_deny == {}:
            self._ufw_status()
        return self._ufw_deny

    def _ufw_status(self):
        _, out, _ = j.sal.process.execute("ufw status")
        for line in out.splitlines():
            if line.find("(v6)") != -1:
                continue
            if line.find("ALLOW ") != -1:
                ip = line.split(" ", 1)[0]
                self._ufw_allow[ip] = "*"
            if line.find("DENY ") != -1:
                ip = line.split(" ", 1)[0]
                self._ufw_deny[ip] = "*"

    def allowIncoming(self, port, protocol="tcp"):
        if self.ufw_enabled == False:
            return
        j.sal.process.execute("ufw allow %s/%s" % (port, protocol))

    def denyIncoming(self, port):
        if self.ufw_enabled == False:
            return
        j.sal.process.execute("ufw deny %s" % port)

    def flush(self):
        if self.ufw_enabled == False:
            return
        C = """
        ufw disable
        iptables --flush
        iptables --delete-chain
        iptables --table nat --flush
        iptables --table filter --flush
        iptables --table nat --delete-chain
        iptables --table filter --delete-chain
        """
        j.sal.process.execute(C)

    def show(self):
        if self.ufw_enabled == False:
            return
        a = self.ufw_rules_allow
        b = self.ufw_rules_deny
        self._log_info("ALLOW")
        self._log_info(a)
        self._log_info("DENY")
        self._log_info(b)

        # self._log_info(j.sal.process.execute("iptables -t nat -nvL"))
