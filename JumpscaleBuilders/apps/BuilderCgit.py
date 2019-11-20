from Jumpscale import j

builder_method = j.baseclasses.builder_method

PACKAGES = """gettext-base,fcgiwrap,git,cgit,highlight,
ca-certificates,nginx,gettext-base,markdown,python3-markdown, 
python3-docutils,groff,libcurl4-openssl-dev,spawn-fcgi"""

NGINX_LOG_DIR = f"/var/log/nginx/log/"
CGIT_SOURCE_DIR = f"/srv/git"
NGINX_CONF = """

server {
    listen       %(port)s;
    server_name  localhost;

    #charset koi8-r;
    #access_log  /var/log/nginx/log/host.access.log  main;

    location / {
      try_files $uri @cgit;
    }

    location @cgit {
      fastcgi_param       SCRIPT_FILENAME /usr/lib/cgit/cgit.cgi;

      fastcgi_param       HTTP_HOST $server_name;
      #fastcgi_split_path_info             ^(/cgit/?)(.+)$;
      #fastcgi_param       PATH_INFO       $fastcgi_path_info;
      fastcgi_param       PATH_INFO       $uri;
      fastcgi_param       QUERY_INFO      $uri;

      include fastcgi_params;

      fastcgi_pass        unix:/var/run/fcgiwrap.socket;
    }

    location /cgit-css/ {
        rewrite ^/cgit-css(/.*)$ $1 break;
        root /usr/share/cgit;
    }

    # deny access to .htaccess files, if Apache's document root
    # concurs with nginx's one
    #
    location ~ /\.ht {
        deny  all;
    }
}
"""

CGITRC_CONFIG = """
#
# cgit config
# see cgitrc(5) for details

root-title=My cgit interface
root-desc=Super fast interface to my git repositories

source-filter=/usr/lib/cgit/filters/syntax-highlighting.sh
about-filter=/usr/lib/cgit/filters/about-formatting.sh

##
## Search for these files in the root of the default branch of repositories
## for coming up with the about page:
##
readme=:README.md
readme=:readme.md
readme=:README.mkd
readme=:readme.mkd
readme=:README.rst
readme=:readme.rst
readme=:README.html
readme=:readme.html
readme=:README.htm
readme=:readme.htm
readme=:README.txt
readme=:readme.txt
readme=:README
readme=:readme
readme=:INSTALL.md
readme=:install.md
readme=:INSTALL.mkd
readme=:install.mkd
readme=:INSTALL.rst
readme=:install.rst
readme=:INSTALL.html
readme=:install.html
readme=:INSTALL.htm
readme=:install.htm
readme=:INSTALL.txt
readme=:install.txt
readme=:INSTALL
readme=:install

# Default Theme
css=/cgit-css/cgit.css
logo=/cgit-css/cgit.png

# Cache
cache-root=/var/cache/cgit
cache-size=1000

enable-index-links=1
enable-index-owner=0
enable-remote-branches=1
enable-log-filecount=1
enable-log-linecount=1
enable-git-config=1
snapshots=tar.gz tar.bz2 zip

robots=noindex, nofollow

virtual-root=/

section-from-path=0

max-repo-count=50

scan-path=/srv/git/

"""

SYNTAX_HIGHLIGHT = """
#!/bin/sh
BASENAME="$1"
EXTENSION="${BASENAME##*.}"

[ "${BASENAME}" = "${EXTENSION}" ] && EXTENSION=txt
[ -z "${EXTENSION}" ] && EXTENSION=txt

# map Makefile and Makefile.* to .mk
[ "${BASENAME%%.*}" = "Makefile" ] && EXTENSION=mk
exec highlight --force -f -I -O xhtml -S "$EXTENSION" 2>/dev/null
"""


class BuilderCgit(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.cgit"

    def _init(self, **kwargs):
        self.DIR_CODE = self._joinpaths(self.DIR_BUILD, "code")
        self.DIR_BIN = "/sandbox/bin"
        self.port = 8008
        self.host = "localhost"  # TODO

    @property
    def startup_cmds(self):
        cgit_server = j.servers.startupcmd.get("cgit")
        cgit_server.cmd_start = (
            f"/usr/bin/spawn-fcgi  -F $(nproc) -M 666 -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap"
        )
        nginx_server = j.servers.startupcmd.get("nginx")
        nginx_server.cmd_start = f"/usr/sbin/nginx -g 'daemon off;'"
        return [cgit_server, nginx_server]

    @builder_method()
    def install(self, reset=True):
        self.system.package.update()
        self.system.package.install(PACKAGES)
        j.sal.fs.createDir(NGINX_LOG_DIR)
        j.sal.fs.createDir(CGIT_SOURCE_DIR)

    # @builder_method()
    def start(self):
        self._write("/etc/nginx/sites-available/default", NGINX_CONF % {"port": self.port})
        self._write("/etc/cgitrc", CGITRC_CONFIG)
        self._write("/usr/lib/cgit/filters/syntax-highlighting.sh", SYNTAX_HIGHLIGHT)
        # TODO disable service when systemd exist for nginx and fcgiwrap services
        # Two steps below added incase systemd is exist
        self._execute("nginx -t;service nginx stop ")
        self._execute("service fcgiwrap  stop ")
        for startupcmd in self.startup_cmds:
            startupcmd.start()
        print("your cgit started successfully on port 8008, connect http://localhost:8008")
        print("you need to clone your repo under /srv/git/ and wait a time to appear in cgit UI")
