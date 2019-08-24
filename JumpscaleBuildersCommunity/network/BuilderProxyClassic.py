from Jumpscale import j
import os
import time

import socket


class BuilderProxyClassic(j.baseclasses.builder):
    """
    all methods to do to allow a local lan to work more efficient with internet e.g. cache for apt-get, web proxy, ...

    this solution is getting outdated, we are working on a much better way

    """

    def removeFromSystemD(self):
        pm = j.builders.system.processmanager.get("systemd")
        pm.remove("polipo")
        pm.remove("privoxy")

    def installFilterProxy(self, port=8124, forward=True):
        """
        installs privoxy
        """
        j.builders.ufw.ufw_enable(force=False)
        j.builders.ufw.allowIncoming(port)
        j.builders.system.package.ensure("privoxy")

        CONFIG = """
            #trust-info-url  http://www.example.com/why_we_block.html
            #admin-address privoxy-admin@example.com
            #confdir /usr/local/etc/privoxy
            confdir /etc/privoxy
            #logdir {DIR_VAR}/privoxy
            logfile logfile

            actionsfile match-all.action # Actions that are applied to all sites and maybe overruled later on.
            actionsfile default.action   # Main actions file
            actionsfile user.action      # User customizations
            filterfile default.filter
            filterfile user.filter      # User customizations

            debug     1 # Log the destination for each request Privoxy let through. See also debug 1024.
            # debug     2 # show each connection status
            # debug     4 # show I/O status
            # debug     8 # show header parsing
            # debug    16 # log all data written to the network
            # debug    32 # debug force feature
            # debug    64 # debug regular expression filters
            debug   128 # debug redirects
            # debug   256 # debug GIF de-animation
            # debug   512 # Common Log Format
            debug  1024 # Log the destination for requests Privoxy didn't let through, and the reason why.
            debug  2048 # CGI user interface
            debug  4096 # Startup banner and warnings.
            debug  8192 # Non-fatal errors
            # debug 32768 # log all data read from the network
            debug 65536 # Log the applying actions

            listen-address  0.0.0.0:$port

            enforce-blocks 1

            #web ui
            #enable-edit-actions 1

            # permit-access  192.168.45.64/26
            # deny-access    192.168.45.73    www.dirty-stuff.example.com

            #if proxy acl's to parent
            enable-proxy-authentication-forwarding 0

            #if parent
            #forward  / localhost:8123
            forward         192.168.*.*/     .
            forward           localhost/     .

            forwarded-connect-retries  0

            accept-intercepted-requests 0


            keep-alive-timeout 5
            tolerate-pipelining 1
            # connection-sharing 1

            """
        CONFIG = CONFIG.replace("$port", str(port))
        CONFIG = j.core.text.strip(CONFIG)

        if forward:
            self.installCacheProxy(force=False)
            CONFIG += "forward  / localhost:8123\n"

        j.sal.fs.writeFile("/etc/privoxy/config", CONFIG)

        self.removeFromSystemD()

        USERACTION = """
            {{alias}}

            +crunch-all-cookies = +crunch-incoming-cookies +crunch-outgoing-cookies
            -crunch-all-cookies = -crunch-incoming-cookies -crunch-outgoing-cookies
             allow-all-cookies  = -crunch-all-cookies -session-cookies-only -filter{content-cookies}
             allow-popups       = -filter{all-popups} -filter{unsolicited-popups}
            +block-as-image     = +block{Blocked image request.} +handle-as-image
            -block-as-image     = -block

            fragile     = -block -crunch-all-cookies -filter -fast-redirects -hide-referer -prevent-compression
            shop        = -crunch-all-cookies allow-popups

            myfilters   = +filter{html-annoyances} +filter{js-annoyances} +filter{all-popups}\
                          +filter{webbugs} +filter{banners-by-size}

            allow-ads   = -block -filter{banners-by-size} -filter{banners-by-link}

            #BLOCK
            {+block{Update stop.} +handle-as-empty-document}
            .apple.com
            .microsoft.com
            *update*
            *download*
            *.mp4
            *.mp3
            *.mkv
            *youtube*
            *youporn*
            *samsung*
            *windows*
            *android*
            *itunes*
            *deezer*
            *.flac
            *tucows*

            +filter{shockwave-flash}
            +filter{crude-parental}

            { allow-all-cookies }

            { -filter{all-popups} }
            .banking.example.com

            #ignore all below
            { -filter }
            .tldp.org
            #/(.*/)?selfhtml/

            { +block{Nasty ads.} }
            www.example.com/nasty-ads/sponsor.gif

            { +block-as-image }
            .doubleclick.net
            /Realmedia/ads/
            ar.atwola.com/

            { fragile }
            .forbes.com

            { allow-ads }
            #.sourceforge.net

            { +set-image-blocker{blank} }

            """

        USERACTION = j.core.text.strip(USERACTION)

        j.sal.fs.writeFile("/etc/privoxy/user.action", USERACTION)

        self.start()

        self._log_info("http://config.privoxy.org/")
        self._log_info("http://config.privoxy.org/show-status")
        self._log_info("http://config.privoxy.org/show-request")
        self._log_info("http://config.privoxy.org/show-url-info")

    def start(self):

        cmd = "privoxy --no-daemon /etc/privoxy/config"
        pm = j.builders.system.processmanager.get("tmux")
        pm.ensure("privoxy", cmd)  # in tmux will always restart

        cmd = "polipo -c /etc/polipo/config"
        pm.ensure("polipo", cmd)  # in tmux will always restart

    def installCacheProxy(self, storagemntpoint="/storage", btrfs=False):

        port = 8123

        j.builders.ufw.ufw_enable(force=False)
        j.builders.ufw.allowIncoming(port)

        if not j.builders.tools.dir_exists(storagemntpoint):
            raise j.exceptions.RuntimeError("Cannot find storage mountpoint:%s" % storagemntpoint)

        cachedir = "%s/polipo_cache" % storagemntpoint

        if btrfs:
            j.builders.storage.btrfs.subvolumeCreate(cachedir)
        else:
            j.core.tools.dir_ensure(cachedir)

        j.builders.system.package.ensure("polipo")

        forbiddentunnels = """
            # simple case, exact match of hostnames
            www.massfuel.com

            # match hostname against regexp
            \.hitbox\.

            # match hostname and port against regexp
            # this will block tunnels to example.com but also  www.example.com
            # for ports in the range 600-999
            # Also watch for effects of 'tunnelAllowedPorts'
            example.com\:[6-9][0-9][0-9]

            # random examples
            \.liveperson\.
            \.atdmt\.com
            .*doubleclick\.net
            .*webtrekk\.de
            ^count\..*
            .*\.offerstrategy\.com
            .*\.ivwbox\.de
            .*adwords.*
            .*\.sitestat\.com
            \.xiti\.com
            webtrekk\..*
            """
        j.sal.fs.writeFile("/etc/polipo/forbiddenTunnels", forbiddentunnels)

        # dnsNameServer

        CONFIG = """
            proxyAddress = "0.0.0.0"    # IPv4 only
            # allowedClients = 127.0.0.1, 134.157.168.57

            #authCredentials = midori:midori

            # parentProxy = "squid.example.org:3128"
            # socksParentProxy = "localhost:9050"
            # socksProxyType = socks5

            # Uncomment this if you want to scrub private information from the log:
            # scrubLogs = true

            ### Memory
            chunkHighMark = 100331648
            objectHighMark = 16384

            ### On-disk data
            diskCacheRoot = "$cachedir"

            ### Domain Name System
            ### ******************

            # Uncomment this if you want to contact IPv4 hosts only (and make DNS
            # queries somewhat faster):
            dnsQueryIPv6 = no

            # Uncomment this to disable Polipo's DNS resolver and use the system's
            # default resolver instead.  If you do that, Polipo will freeze during
            # every DNS query:
            # dnsUseGethostbyname = yes


            ### HTTP
            ### ****

            # Uncomment this if you want to enable detection of proxy loops.
            # This will cause your hostname (or whatever you put into proxyName
            # above) to be included in every request:

            # disableVia=false

            # Uncomment this if you want to slightly reduce the amount of
            # information that you leak about yourself:

            # censoredHeaders = from, accept-language
            censorReferer = maybe

            # Uncomment this if you're paranoid.  This will break a lot of sites,
            # though:

            # censoredHeaders = set-cookie, cookie, cookie2, from, accept-language
            # censorReferer = true

            # Uncomment this if you want to use Poor Man's Multiplexing; increase
            # the sizes if you're on a fast line.  They should each amount to a few
            # seconds' worth of transfer; if pmmSize is small, you'll want
            # pmmFirstSize to be larger.

            # Note that PMM is somewhat unreliable.

            # pmmFirstSize = 16384
            # pmmSize = 8192

            # Uncomment this if your user-agent does something reasonable with
            # Warning headers (most don't):

            relaxTransparency = maybe

            # Uncomment this if you never want to revalidate instances for which
            # data is available (this is not a good idea):

            # relaxTransparency = yes

            # Uncomment this if you have no network:

            # proxyOffline = yes

            # Uncomment this if you want to avoid revalidating instances with a
            # Vary header (this is not a good idea):

            # mindlesslyCacheVary = true

            # Uncomment this if you want to add a no-transform directive to all
            # outgoing requests.

            # alwaysAddNoTransform = true

            disableIndexing = false

            #enable-compression 1
            #can be till 9
            #compression-level 9

            """

        CONFIG = CONFIG.replace("$cachedir", cachedir)
        j.sal.fs.writeFile("/etc/polipo/config", CONFIG)

        j.sal.process.execute("killall polipo", die=False)

        _, cmd, _ = j.sal.process.execute("which polipo")

        self._log_info("INSTALL OK")
        self._log_info("to see status: point webbrowser to")
        self._log_info("http://%s:%s/polipo/status?" % (j.builders.tools.executor.addr, port))
        self._log_info(
            "configure your webproxy client to use %s on tcp port %s" % (j.builders.tools.executor.addr, port)
        )

        self.removeFromSystemD(force=False)

    def configureClient(self, addr="", port=8123):
        if addr == "":
            addr = j.builders.executor.addr
        config = 'Acquire::http::Proxy "http://%s:%s";' % (addr, port)
        if j.builders.prefab.platformtype.myplatform.startswith("ubuntu"):
            f = j.core.tools.file_text_read("/etc/apt/apt.conf", "")
            f += "\n%s\n" % config
            j.sal.fs.writeFile("/etc/apt/apt.conf", f)
        else:
            raise j.exceptions.Base("not implemented yet")

    def __str__(self):
        return "prefab.proxy:%s:%s" % (getattr(self.executor, "addr", "local"), getattr(self.executor, "port", ""))

    __repr__ = __str__
