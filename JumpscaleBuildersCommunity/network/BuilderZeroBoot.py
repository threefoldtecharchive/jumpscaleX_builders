import re
import time

from Jumpscale import j


ZEROTIER_FIREWALL_ZONE_REGEX = re.compile(r"^firewall\.@zone\[(\d+)\]\.name='zerotier'$")
FORWARDING_FIREWALL_REGEX = re.compile(r"^firewall\.@forwarding\[(\d+)\].*?('\w+')?$")


class BuilderZeroBoot(j.baseclasses.builder):
    def install(self, network_id, token, zos_version="v.1.4.1", zos_args="", reset=False):
        if not reset and self._done_check("install"):
            return
        # update zerotier config
        j.builders.network.zerotier.build(install=True, reset=reset)

        # Remove sample_config
        rc, _, _ = j.sal.process.execute("uci show zerotier.sample_config", die=False)
        if rc == 0:
            j.sal.process.execute("uci delete zerotier.sample_config")
            j.sal.process.execute("uci commit")

        # Add our config
        if reset:
            zerotier_reinit = True
        else:
            rc, out, _ = j.sal.process.execute("uci show zerotier.config", die=False)
            zerotier_reinit = rc  # rc == 1 if configuration is not present
            if not zerotier_reinit:
                # Check if the configuration matches our expectations
                if not "zerotier.config.join='{}'".format(network_id) in out:
                    zerotier_reinit = True
        if zerotier_reinit:
            # Start zerotier at least one time to generate config files
            j.sal.process.execute("uci set zerotier.config=zerotier")
            j.sal.process.execute("uci set zerotier.config.enabled='1'")
            j.sal.process.execute("uci set zerotier.config.interface='wan'")  # restart ZT when wan status changed
            j.sal.process.execute("uci add_list zerotier.config.join='{}'".format(network_id))  # Join zerotier network
            j.sal.process.execute("uci set zerotier.config.secret='generate'")  # Generate secret on the first start
            j.sal.process.execute("uci commit")
            j.sal.process.execute("/etc/init.d/zerotier enable")
            j.sal.process.execute("/etc/init.d/zerotier start")

        # Join Network
        zerotier_client = j.clients.zerotier.get(data={"token_": token})
        j.builders.network.zerotier.network_join(network_id, zerotier_client=zerotier_client)

        # update TFTP and DHCP
        j.sal.process.execute("uci set dhcp.@dnsmasq[0].enable_tftp='1'")
        j.sal.process.execute("uci set dhcp.@dnsmasq[0].tftp_root='/opt/storage/'")
        j.sal.process.execute("uci set dhcp.@dnsmasq[0].dhcp_boot='pxelinux.0'")
        j.sal.process.execute("uci commit")

        j.core.tools.dir_ensure("/opt/storage")
        j.sal.process.execute("opkg install curl ca-bundle")
        j.sal.process.execute("curl https://download.gig.tech/pxe.tar.gz -o /opt/storage/pxe.tar.gz")
        j.sal.process.execute("tar -xzf /opt/storage/pxe.tar.gz -C /opt/storage")
        j.sal.process.execute("cp -r /opt/storage/pxe/* /opt/storage")
        j.sal.process.execute("rm -rf /opt/storage/pxe")
        j.sal.process.execute(
            'sed -i "s|a84ac5c10a670ca3|%s/%s|g" /opt/storage/pxelinux.cfg/default' % (network_id, zos_args)
        )
        j.sal.process.execute('sed -i "s|zero-os-master|%s|g" /opt/storage/pxelinux.cfg/default' % zos_version)

        # this is needed to make sure that network name is ready
        for _ in range(12):
            try:
                network_device_name = j.builders.network.zerotier.get_network_interface_name(network_id)
                break
            except KeyError:
                time.sleep(5)
        else:
            raise j.exceptions.Base("Unable to join network within 60 seconds!")
        j.sal.process.execute("uci set network.{0}=interface".format(network_device_name))
        j.sal.process.execute("uci set network.{0}.proto='none'".format(network_device_name))
        j.sal.process.execute("uci set network.{0}.ifname='{0}'".format(network_device_name))

        try:
            zone_id = self.get_zerotier_firewall_zone()
        except KeyError:
            j.sal.process.execute("uci add firewall zone")
            zone_id = -1

        j.sal.process.execute("uci set firewall.@zone[{0}]=zone".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].input='ACCEPT'".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].output='ACCEPT'".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].name='zerotier'".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].forward='ACCEPT'".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].masq='1'".format(zone_id))
        j.sal.process.execute("uci set firewall.@zone[{0}].network='{1}'".format(zone_id, network_device_name))

        self.add_forwarding("lan", "zerotier")
        self.add_forwarding("zerotier", "lan")

        j.sal.process.execute("uci commit")

        self._done_set("install")

    def get_zerotier_firewall_zone(self):
        _, out, _ = j.sal.process.execute("uci show firewall")
        for line in out.splitlines():
            m = ZEROTIER_FIREWALL_ZONE_REGEX.match(line)
            if m:
                return int(m.group(1))
        raise j.exceptions.NotFound("Zerotier zone in firewall configuration was not found!")

    def add_forwarding(self, dest, src):
        _, out, _ = j.sal.process.execute("uci show firewall")
        forwards = dict()
        for line in out.splitlines():
            m = FORWARDING_FIREWALL_REGEX.match(line)
            if m:
                if line.endswith("=forwarding"):
                    forwards[m.group(1)] = dict()
                elif ".dest=" in line:
                    forwards[m.group(1)]["dest"] = m.group(2)
                elif ".src=" in line:
                    forwards[m.group(1)]["src"] = m.group(2)
        if {"dest": "'%s'" % dest, "src": "'%s'" % src} in forwards.values():
            return
        j.sal.process.execute("uci add firewall forwarding")
        j.sal.process.execute("uci set firewall.@forwarding[-1]=forwarding")
        j.sal.process.execute("uci set firewall.@forwarding[-1].dest='%s'" % dest)
        j.sal.process.execute("uci set firewall.@forwarding[-1].src='%s'" % src)
