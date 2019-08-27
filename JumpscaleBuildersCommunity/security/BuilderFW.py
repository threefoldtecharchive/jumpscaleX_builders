from Jumpscale import j


class BuilderFW(j.baseclasses.builder):
    def _init(self, **kwargs):
        self._fw_enabled = None
        self._fw_type = None

    @property
    def fw_type(self):
        if self._fw_type is None:
            if j.core.platformtype.myplatform.platform_is_osx:
                raise j.exceptions.Input(
                    message="cannot enable fw, mac  not supported ", level=1, source="", tags="", msgpub=""
                )

                if self.tools.command_check("nft") is not False:
                    self._fw_type = "nft"
                else:
                    raise NotImplemented("only support nft for now")

        return self._fw_type

    def allowIncoming(self, port, protocol="tcp"):
        """as alternative on ufw"""
        if j.core.platformtype.myplatform.platform_is_osx:
            return
        j.sal.process.execute(
            "nft add rule filter input {protocol} dport {port} log accept".format(protocol=protocl, port=port)
        )

    def denyIncoming(self, port):
        if j.core.platformtype.myplatform.platform_is_osx:
            return
        j.sal.process.execute(
            "nft add rule filter input {protocol} dport {port} log reject".format(protocol=protocl, port=port)
        )

    def flush(self, permanent=False):
        j.sal.process.execute("nft flush ruleset")
        if permanent:
            self.setRuleset("")

    def show(self):
        rc, out = j.sal.process.execute("nft list ruleset")

    def getRuleset(self):
        rc, out, err = j.sal.process.execute("nft list ruleset", showout=False)
        return out

    def setRuleset(self, ruleset, pinghost="8.8.8.8"):
        if not j.builders.system.net.ping(pinghost):
            raise j.exceptions.Input(
                message="Cannot set firewall ruleset if we cannot ping to the host we have to check against.",
                level=1,
                source="",
                tags="",
                msgpub="",
            )
        rc, currentruleset, err = j.sal.process.execute("nft list ruleset")
        if ruleset in currentruleset:
            return

        pscript = """
        C='''
        $ruleset
        '''
        import os
        import time

        rc=os.system("nft list ruleset > /tmp/firelwallruleset_old")
        if rc>0:
            raise j.exceptions.Base("Cannot export firelwall ruleset")

        f = open('/etc/nftables.conf', 'w')
        f.write(C)

        #now applying
        self._log_info("applied ruleset")
        rc=os.system("nft -f /etc/nftables.conf")
        time.sleep(1)

        rc2=os.system("ping -c 1 $pinghost")

        if rc2!=0:
            self._log_info("could not apply, restore")
            #could not ping need to restore
            os.system("cp /tmp/firelwallruleset_old /etc/nftables.conf")
            rc=os.system("nft -f /etc/nftables.conf")

        if rc>0 or rc2>0:
            raise j.exceptions.Base("Could not set interface file, something went wrong, previous situation restored.")


        """
        pscript = j.core.text.strip(pscript)
        pscript = pscript.replace("$ruleset", ruleset)
        pscript = pscript.replace("$pinghost", pinghost)

        self._execute(content=pscript, die=True, interpreter="python3", tmux=True)
