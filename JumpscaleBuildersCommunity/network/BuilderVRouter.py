from Jumpscale import j
import os
import time

import socket


class BuilderVRouter(j.baseclasses.builder):
    """
    """

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
        self._defgwInterface = None
        self._check = False

    def check(self):
        if self._check is False:
            if not j.builders.platformtype.myplatform.startswith("ubuntu"):
                raise j.exceptions.Input(message="only support ubuntu for now")
        self._check = "OK"

    @property
    def defgwInterface(self):
        if self._defgwInterface is None:
            self._defgwInterface = j.builders.system.net.defaultgwInterface
        return self._defgwInterface

    def runSolution(self):
        self.prepare()
        self.bridge()
        self.dnsServer()
        self.dhcpServer()
        self.firewall()
        self.hostap()
        self.accesspoint()
        self.proxy()

    def prepare(self):
        j.builders.system.package.ensure("inetutils-ping")
        j.builders.system.package.ensure("nftables")
        self.check()
        j.builders.systemservices.fw.flush(permanent=True)

        # will make sure jumpscale has been installed (&base)
        j.builders.development.js8.install()

        dest = self._replace("{DIR_CODE}/github/threefoldtech/jumpscale_smartproxy")
        j.clients.git.pullGitRepo("git@github.com:despiegk/smartproxy.git", dest=dest)

        j.builders.tools.upload("{DIR_CODE}/github/threefoldtech/jumpscale_smartproxy")
        C = """
        rm -rf /opt/dnsmasq-alt
        ln -sf {DIR_CODE}/github/threefoldtech/jumpscale_smartproxy /opt/dnsmasq-alt
        """
        j.sal.process.execute(C)

        config = """
        net.ipv4.ip_forward=1
        """
        # make sure it works at runtime
        j.sal.fs.writeFile("/etc/sysctl.d/90-ipforward.conf", config)
        j.sal.process.execute("sysctl --system")
        j.sal.process.execute("nft -f /etc/nftables.conf")
        # firewall is now empty

    def bridge(self):
        """
        create bridge which has accesspoint interface in it (wireless)
        """
        ipaddr = "%s.254" % self.freeNetworkRangeDMZ

        try:
            if ipaddr in j.builders.system.net.getInfo("br0")["ip"]:
                return
        except BaseException:
            pass

        C = """
        auto br0
        iface br0 inet static
          address $range.254
          netmask 255.255.255.0
          bridge_ports $iface
        """
        self.check()
        C = C.replace("$iface", self.wirelessInterfaceNonDefGW)
        C = C.replace("$range", self.freeNetworkRangeDMZ)
        C = j.core.text.strip(C)
        I = j.core.tools.file_text_read("/etc/network/interfaces")
        OUT = ""
        state = ""
        for l in I.split("\n"):
            if l.startswith("auto br0"):
                state = "skip"
                continue
            elif l.startswith("iface br0"):
                state = "skip"
                continue
            if l.strip() == "":
                state = ""
            if state == "skip":
                continue
            OUT += "%s\n" % l
        OUT += C
        j.builders.system.net.setInterfaceFile(OUT)

        if ipaddr not in j.builders.system.net.getInfo("br0")["ip"]:
            raise j.exceptions.RuntimeError(
                "could not set bridge, something went wrong, could not find ip addr:%s" % ipaddr
            )

    def dnsServer(self):
        self.check()
        j.builders.system.tmux.createSession("ovsrouter", ["dns"], returnifexists=True, killifexists=False)
        j.builders.system.process.kill("dns-server")
        cmd = "jspython /opt/dnsmasq-alt/dns-server.py"
        j.builders.system.tmux.executeInScreen("ovsrouter", "dns", cmd)

    @property
    def wirelessInterfaceNonDefGW(self):
        """
        find wireless interface which is not the def gw
        needs to be 1
        """
        interfaces = [item for item in j.builders.system.net.wirelessLanInterfaces if item != self.defgwInterface]
        if len(interfaces) != 1:
            raise j.exceptions.Input(
                message="Can only create access point if 1 wireless interface found which is not the default gw.",
                level=1,
                source="",
                tags="",
                msgpub="",
            )
        return interfaces[0]

    @property
    def freeNetworkRangeDMZ(self):
        """
        look for free network range
        default: 192.168.86.0/24
        and will go to 87... when not available
        """
        return "192.168.86"
        # for i in range(100, 150):
        #     iprange = "192.168.%s" % i
        #     for item in j.builders.system.net.ips:
        #         if not item.startswith(iprange):
        #             return iprange
        # raise j.exceptions.Input(message="Cannot find free dmz iprange")

    def dhcpServer(self, interfaces=[]):
        """
        will run dhctp server in tmux on interfaces specified
        if not specified then will look for wireless interface which is used in accesspoint and use that one
        """
        self.check()
        j.builders.system.package.ensure("isc-dhcp-server")
        if interfaces == []:
            interfaces = [self.wirelessInterfaceNonDefGW]
        r = self.freeNetworkRangeDMZ
        config = """
        subnet $range.0 netmask 255.255.255.0 {
          range $range.100 $range.200;
          option domain-name-servers $range.254;
          option subnet-mask 255.255.255.0;
          option routers $range.254;
          option broadcast-address $range.255;
          default-lease-time 600;
          max-lease-time 7200;
        }
        """
        config = config.replace("$range", r)
        j.sal.fs.writeFile("/etc/dhcp/dhcpd.conf", config)

        C = """
        killall dhcpd
        rm /var/lib/dhcp/dhcpd.leases
        touch /var/lib/dhcp/dhcpd.leases
        """
        j.sal.process.execute(C)

        cmd = "dhcpd -f"
        j.builders.system.tmux.executeInScreen("ovsrouter", "dhcpd", cmd)

    def hostap(self):
        self.check()
        """
        install hostaccesspoint (build)
        """
        C = """
        #!/bin/bash
        set -x

        add-apt-repository ppa:hanipouspilot/rtlwifi
        apt-get update
        apt-get install -y rtl8192eu-dkms

        mkdir /opt/netpoc
        cd /opt/netpoc

        wget -c http://w1.fi/releases/hostapd-2.5.tar.gz
        rm -rfv hostapd-2.5/
        tar -xvf hostapd-2.5.tar.gz

        apt-get install -y libnl-3-dev libnl-genl-3-dev pkg-config libssl-dev
        git clone --depth=1 https://github.com/pritambaral/hostapd-rtl871xdrv.git

        cd /opt/netpoc/hostapd-2.5/hostapd
        cp defconfig .config

        sed -i s/'#CONFIG_LIBNL32=y'/'CONFIG_LIBNL32=y'/g .config
        make # compile first to be sur it works without patch

        cd ..
        patch -Np1 -i ../hostapd-rtl871xdrv/rtlxdrv.patch
        cd hostapd

        echo CONFIG_DRIVER_RTW=y >> .config
        make clean && make
        """
        j.sal.process.execute(C)

    def accesspoint(self, sid="internet", passphrase="helloworld"):
        """
        will look for free wireless interface which is not the def gw
        this interface will be used to create an accesspoint
        """
        self.check()

        C = """
        interface=$iface
        #driver=rtl871xdrv
        bridge=br0
        ctrl_interface=/var/run/hostapd
        ssid=Green 2
        hw_mode=g
        wmm_enabled=1
        channel=1
        wpa=2
        wpa_key_mgmt=WPA-PSK
        wpa_pairwise=TKIP
        rsn_pairwise=CCMP
        auth_algs=1
        wpa_passphrase=$passphrase
        """
        C = C.replace("$iface", self.wirelessInterfaceNonDefGW)
        C = C.replace("$passphrase", passphrase)
        configdest = "/etc/hostapd.conf"
        j.sal.fs.writeFile(configdest, C)

        cmd = "/opt/netpoc/hostapd-2.5/hostapd/hostapd %s" % configdest
        j.builders.system.tmux.executeInScreen("ovsrouter", "ap", cmd)

    def firewall(self):
        path = "{DIR_CODE}/github/threefoldtech/jumpscale_smartproxy/nftables.conf"
        # needs to be from local file
        C = j.sal.fs.readFile(j.dirs.replace_txt_dir_vars(path))
        C = C.replace("$waniface", self.defgwInterface)
        C = C.replace("$range", self.freeNetworkRangeDMZ)
        j.builders.systemservices.fw.setRuleset(C)

    def proxy(self):
        C = """
        apt-get install python-pip python-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev -y
        pip3 install cffi
        """

        cmd = "python3 mitmproxy_start.py -T -d -d -p 8443 -s /opt/dnsmasq-alt/http-filter.py"
        j.builders.system.tmux.executeInScreen("ovsrouter", "proxy", cmd)

    #
    # def accesspointAllInOne(self, passphrase, name="", dns="8.8.8.8", interface="wlan0"):
    #     """
    #     create an accesspoint with 1 script, do not use if you are using our smarter mitmproxy
    #     """
    #
    #     # create_ap --no-virt -m bridge wlan1 eth0 kds10 kds007kds
    #     # sysctl -w net.ipv4.ip_forward=1
    #     # iptables -t nat -I POSTROUTING -o wlan0 -j MASQUERADE
    #
    #     # cmd1='dnsmasq -d'
    #     if name != "":
    #         hostname = name
    #     else:
    #         _, hostname, _ = j.sal.process.execute("hostname")
    #     #--dhcp-dns 192.168.0.149
    #     _, cpath, _ = j.sal.process.execute("which create_ap")
    #     cmd2 = '%s %s eth0 gig_%s %s -d' % (cpath, interface, hostname, passphrase)
    #
    #     giturl = "https://github.com/oblique/create_ap"
    #     j.builders.pullGitRepo(url=giturl, dest=None, login=None, passwd=None, depth=1,
    #                               ignorelocalchanges=True, reset=True, branch=None, revision=None, ssh=False)
    #
    #     j.sal.process.execute("cp /sandbox/code/create_ap/create_ap /usr/local/bin/")
    #
    #     START1 = """
    #     [Unit]
    #     Description = Create AP Service
    #     Wants = network - online.target
    #     After = network - online.target
    #
    #     [Service]
    #     Type = simple
    #     ExecStart =$cmd
    #     KillSignal = SIGINT
    #     Restart = always
    #     RestartSec = 5
    #
    #     [Install]
    #     WantedBy = multi - user.target
    #     """
    #     pm = j.builders.system.processmanager.get("systemd")
    #     pm.ensure("ap", cmd2, descr="accesspoint for local admin", systemdunit=START1)

    def __str__(self):
        return "prefab.vrouter:%s:%s" % (getattr(self.executor, "addr", "local"), getattr(self.executor, "port", ""))

    __repr__ = __str__
