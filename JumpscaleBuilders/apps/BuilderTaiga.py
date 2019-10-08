from Jumpscale import j

builder_method = j.baseclasses.builder_method


PACKAGES = """build-essential,binutils-doc,autoconf,flex,bison,libjpeg-dev,
libfreetype6-dev,zlib1g-dev,libzmq3-dev,libgdbm-dev,libncurses5-dev,
automake,libtool,gettext,nginx,virtualenvwrapper"""

TAIGA_USER = "taiga"

NGINX_LOG_DIR = f"/home/{TAIGA_USER}/logs"

MEDIA_CONF_FILE = """
from .common import *

MEDIA_URL = "http://localhost/media/"
STATIC_URL = "http://localhost/static/"
SITES["front"]["scheme"] = "http"
SITES["front"]["domain"] = "localhost"

SECRET_KEY = "theveryultratopsecretkey"

DEBUG = False
PUBLIC_REGISTER_ENABLED = True

DEFAULT_FROM_EMAIL = "no-reply@example.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

#CELERY_ENABLED = True

EVENTS_PUSH_BACKEND = "taiga.events.backends.rabbitmq.EventsPushBackend"
EVENTS_PUSH_BACKEND_OPTIONS = {"url": "amqp://taiga:PASSWORD_FOR_EVENTS@localhost:5672/taiga"}

# Uncomment and populate with proper connection parameters
# for enable email sending. EMAIL_HOST_USER should end by @domain.tld
#EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
#EMAIL_USE_TLS = False
#EMAIL_HOST = "localhost"
#EMAIL_HOST_USER = ""
#EMAIL_HOST_PASSWORD = ""
#EMAIL_PORT = 25

# Uncomment and populate with proper connection parameters
# for enable github login/singin.
#GITHUB_API_CLIENT_ID = "yourgithubclientid"
#GITHUB_API_CLIENT_SECRET = "yourgithubclientsecret"
"""

NGINX_CONF = """
server {
    listen %(port)s default_server;
    server_name _;

    large_client_header_buffers 4 32k;
    client_max_body_size 50M;
    charset utf-8;

    access_log %(log_dir)s/nginx.access.log;
    error_log %(log_dir)s/nginx.error.log;

    # Frontend
    location / {
        root %(front_end)s/dist/;
        try_files $uri $uri/ /index.html;
    }

    # Backend
    location /api {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://127.0.0.1:8001/api;
        proxy_redirect off;
    }

    # Admin access (/admin/)
    location /admin {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://127.0.0.1:8001$request_uri;
        proxy_redirect off;
    }

    # Static files
    location /static {
        alias %(back_end)s/static;
    }

    # Media files
    location /media {
        alias %(back_end)s/media;
    }

    # Events
    location /events {
        proxy_pass http://127.0.0.1:8888/events;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
"""


class BuilderTaiga(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.taiga"

    def _init(self, **kwargs):
        self.DIR_CODE = self.tools.joinpaths(self.DIR_BUILD, "code")
        self.frontend_repo_dir = f"{self.DIR_CODE}/taiga-front-dist"
        self.backend_repo_dir = f"{self.DIR_CODE}/taiga-back"
        self.TAIGA_USER = "taiga"
        self.port = 4321
        self.host = "localhost"  # TODO
        self.protocol = "http"

    @builder_method()
    def install_deps(self, reset=False):
        self.system.package.update()
        self.system.package.install(PACKAGES)
        j.builders.db.redis.install(reset=reset)
        j.builders.db.psql.install(reset=reset)
        j.builders.db.psql.start()
        create_user_cmd = f"""
        adduser --system --quiet --shell /bin/bash --group --gecos "taiga user" {TAIGA_USER}
        adduser {TAIGA_USER} sudo
        """
        self._execute(create_user_cmd)

        if not self._done_check("postgresuser"):
            create_psql_user_cmd = """
            sudo -u postgres {DIR_BIN}/createuser -h localhost {TAIGA_USER}
            sudo -u postgres {DIR_BIN}/createdb {TAIGA_USER} -h localhost -O {TAIGA_USER} --encoding='utf-8' --locale=en_US.utf8 --template=template0
            """
            self._execute(create_psql_user_cmd)
            self._done_set("postgresuser")

    @builder_method()
    def backend_install(self):
        j.clients.git.pullGitRepo("https://github.com/taigaio/taiga-back.git", self.backend_repo_dir, branch="stable")
        command = f"""
        chown -R {TAIGA_USER} {self.backend_repo_dir}
        su - {TAIGA_USER} -c '
        cd {self.backend_repo_dir}
        source /usr/share/virtualenvwrapper/virtualenvwrapper_lazy.sh
        mkvirtualenv -p /usr/bin/python3 taiga
        pip3 install -r requirements.txt
        python3 manage.py migrate --noinput
        python3 manage.py loaddata initial_user
        python3 manage.py loaddata initial_project_templates
        python3 manage.py compilemessages
        python3 manage.py collectstatic --noinput
        '
        """
        self._execute(command)
        j.sal.fs.writeFile(f"{self.backend_repo_dir}/settings/local.py", MEDIA_CONF_FILE)

    @builder_method()
    def frontend_install(self):
        j.clients.git.pullGitRepo(
            "https://github.com/taigaio/taiga-front-dist.git", self.frontend_repo_dir, branch="stable"
        )
        conf_dict = j.data.serializers.json.load(f"{self.frontend_repo_dir}/dist/conf.example.json")
        conf_dict["api"] = f"{self.protocol}://{self.host}:{self.port}/api/v1/"
        j.data.serializers.json.dump(f"{self.frontend_repo_dir}/dist/conf.json", conf_dict)

    @builder_method()
    def install(self, reset=True):
        self.install_deps(reset=reset)
        self.backend_install()
        j.sal.fs.createDir(NGINX_LOG_DIR)
        self.frontend_install()

    # @builder_method()
    def start(self):
        j.sal.fs.writeFile(
            "/etc/nginx/conf.d/taiga.conf",
            NGINX_CONF
            % {
                "port": self.port,
                "log_dir": NGINX_LOG_DIR,
                "back_end": self.backend_repo_dir,
                "front_end": self.frontend_repo_dir,
            },
        )
        self._execute("nginx -t && service nginx restart")
        for startupcmd in self.startup_cmds:
            startupcmd.start()

    @property
    def startup_cmds(self):
        taiga_server = j.servers.startupcmd.get("taiga")
        taiga_server.path = f"{self.backend_repo_dir}"
        taiga_server.cmd_start = f"su {TAIGA_USER} -c '/home/{TAIGA_USER}/.virtualenvs/{TAIGA_USER}/bin/gunicorn --workers 4 --timeout 60 -b 127.0.0.1:8001 taiga.wsgi'"
        return [taiga_server]
