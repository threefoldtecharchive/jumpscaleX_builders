from Jumpscale import j
from JumpscaleBuilders.runtimes.BuilderGolangTools import BuilderGolangTools

builder_method = j.baseclasses.builder_method


ALL_PLUGINS = {
    "realip": "github.com/captncraig/caddy-realip",
    "git": "github.com/abiosoft/caddy-git",
    "proxyprotocol": "github.com/mastercactapus/caddy-proxyprotocol",
    "locale": "github.com/simia-tech/caddy-locale",
    "cache": "github.com/nicolasazrak/caddy-cache",
    "authz": "github.com/casbin/caddy-authz",
    "filter": "github.com/echocat/caddy-filter",
    "minify": "github.com/hacdias/caddy-minify",
    "ipfilter": "github.com/pyed/ipfilter",
    "ratelimit": "github.com/xuqingfeng/caddy-rate-limit",
    "search": "github.com/pedronasser/caddy-search",
    "expires": "github.com/epicagency/caddy-expires",
    "cors": "github.com/captncraig/cors/caddy",
    "nobots": "github.com/Xumeiquer/nobots",
    "login": "github.com/tarent/loginsrv/caddy",
    "reauth": "github.com/freman/caddy-reauth",
    "jwt": "github.com/BTBurke/caddy-jwt",
    "jsonp": "github.com/pschlump/caddy-jsonp",
    "upload": "blitznote.com/src/caddy.upload",
    "multipass": "github.com/namsral/multipass/caddy",
    "datadog": "github.com/payintech/caddy-datadog",
    "prometheus": "github.com/miekg/caddy-prometheus",
    "cgi": "github.com/jung-kurt/caddy-cgi",
    # "filemanager": "github.com/filebrowser/filebrowser",
    "iyofilemanager": "github.com/itsyouonline/filemanager/caddy/filemanager",
    "webdav": "github.com/hacdias/caddy-webdav",
    "jekyll": "github.com/hacdias/filemanager/caddy/jekyll",
    "hugo": "github.com/hacdias/filemanager/caddy/hugo",
    "mailout": "github.com/SchumacherFM/mailout",
    "awses": "github.com/miquella/caddy-awses",
    "awslambda": "github.com/coopernurse/caddy-awslambda",
    "grpc": "github.com/pieterlouw/caddy-grpc",
    "gopkg": "github.com/zikes/gopkg",
    "restic": "github.com/restic/caddy",
    "iyo": "github.com/itsyouonline/caddy-integration/oauth",
    "dns": "github.com/coredns/coredns",
    "wsproxy": "github.com/incubaid/wsproxy",
}


PLUGIN_DIRECTIVES = {"iyo": "oauth", "dns": "dns", "wsproxy": "wsproxy"}


# see https://github.com/caddyserver/caddy#build
CADDY_RUNNER = """
package main

import (
	"github.com/caddyserver/caddy/caddy/caddymain"

	// plug in plugins here, for example:
%s
)

func main() {
	// optional: disable telemetry
	// caddymain.EnableTelemetry = false
	caddymain.Run()
}"""


class BuilderCaddy(BuilderGolangTools):
    __jslocation__ = "j.builders.web.caddy"
    PLUGINS = ["iyo"]  # PLEASE ADD MORE PLUGINS #TODO:*1
    VERSION = "master"  # make sure the way to build with plugin is ok

    def _init(self, **kwargs):
        super()._init()
        self.package_path = self.package_path_get("caddyserver/caddy")

    def clean(self):
        self._init()
        j.builders.tools.dir_remove("{DIR_BIN}/caddy")
        C = """
        cd /sandbox
        rm -rf {DIR_BUILD}
        """
        self._execute(C)

    def get_plugin(self, name):
        """get a supported plugin

        :param name: name
        :type name: str
        :raises j.exceptions.RuntimeError: in case the plugin not supported
        """

        if name not in ALL_PLUGINS:
            raise j.exceptions.RuntimeError("plugin not supported")

        url = ALL_PLUGINS[name]
        self.get(url, install=False)

    def profile_builder_set(self):
        super().profile_builder_set()
        self.profile.env_set("GO111MODULE", "on")

    @builder_method()
    def build(self, plugins=None):
        """
        Get/Build the binaries of caddy itself.

        :param plugins: list of plugins names to be installed, defaults to None
        :type plugins: list, optional
        :raises j.exceptions.RuntimeError: if platform is not supported
        """
        if not j.core.platformtype.myplatform.platform_is_ubuntu:
            raise j.exceptions.RuntimeError("only ubuntu supported")

        # install go runtime
        j.builders.runtimes.golangtools.install()

        # get caddy and plugins
        if not plugins:
            plugins = self.PLUGINS

        for plugin in plugins:
            self.get_plugin(plugin)

        # build caddy with a plugins
        plugin_imports = "\n".join(['\t_ "%s"' % ALL_PLUGINS[name] for name in plugins])

        self.get("github.com/caddyserver/caddy/caddy@%s" % self.VERSION)
        runner_file = self._replace("{DIR_BUILD}/caddy.go")
        self.tools.file_write(runner_file, CADDY_RUNNER % plugin_imports)
        self._execute("cd {DIR_BUILD} && gofmt caddy.go && go mod init caddy && go install")

    @builder_method()
    def install(self, plugins=None):
        """
        will build if required & then install binary on right location

        :param plugins: plugins to build with if not build already, defaults to None

        kosmos 'j.builders.web.caddy.install()'

        """

        caddy_bin_path = self.tools.joinpaths(self.DIR_GO_PATH_BIN, self.NAME)
        j.builders.tools.file_copy(caddy_bin_path, "{DIR_BIN}/caddy")

    @property
    def startup_cmds(self):
        cmd = j.servers.startupcmd.get("caddy", cmd_start="caddy", path="/sandbox/bin")
        return [cmd]

    @builder_method()
    def sandbox(self, reset=False, zhub_client=None, flist_create=False):
        bin_dest = j.sal.fs.joinPaths("/sandbox/var/build", "{}/sandbox".format(self.DIR_SANDBOX))
        self.tools.dir_ensure(bin_dest)
        caddy_bin_path = self.tools.joinpaths(self.package_path, "/caddy", self.NAME)
        self.tools.file_copy(caddy_bin_path, bin_dest)

    def _test(self, name=""):
        """Run tests under tests directory

        :param name: basename of the file to run, defaults to "".
        :type name: str, optional
        """
        self._test_run(name=name, obj_key="test_main")
