from Jumpscale import j

builder_method = j.baseclasses.builder_method


PACKAGES = """build-essential,binutils-doc,autoconf,flex,bison,libjpeg-dev,
libfreetype6-dev,zlib1g-dev,libzmq3-dev,libgdbm-dev,libncurses5-dev,
automake,libtool,gettext,nginx,virtualenvwrapper,rabbitmq-server"""

TAIGA_USER = "taiga"

NGINX_LOG_DIR = f"/home/{TAIGA_USER}/logs"

MEDIA_CONF_FILE = """
from .common import *

MEDIA_URL = "http://localhost/media/"
STATIC_URL = "http://localhost/static/"
SITES["front"]["scheme"] = "http"
SITES["front"]["domain"] = "localhost"

SECRET_KEY = %(PASSWORD_FOR_EVENTS)s

DEBUG = False
PUBLIC_REGISTER_ENABLED = True

DEFAULT_FROM_EMAIL = "no-reply@example.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

#CELERY_ENABLED = True

EVENTS_PUSH_BACKEND = "taiga.events.backends.rabbitmq.EventsPushBackend"
EVENTS_PUSH_BACKEND_OPTIONS = {"url": "amqp://taiga:%(PASSWORD_FOR_EVENTS)s@localhost:5672/taiga"}

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
        self.DIR_CODE = self._joinpaths(self.DIR_BUILD, "code")
        self.DIR_BIN = j.core.tools.text_replace("{DIR_BASE}/bin")
        self.frontend_repo_dir = f"{self.DIR_CODE}/taiga-front-dist"
        self.backend_repo_dir = f"{self.DIR_CODE}/taiga-back"
        self.events_repo_dir = f"{self.DIR_CODE}/taiga-event"
        self.TAIGA_USER = "taiga"
        self.port = 4321
        self.host = "localhost"  # TODO
        self.protocol = "http"

    @builder_method()
    def clean(self):
        j.builders.db.psql.clean()
        self._remove(self.DIR_BUILD)
        cmd = """
        deluser taiga
        rabbitmqctl delete_user taiga
        rabbitmqctl delete_vhost taiga
        service rabbitmq-server stop
        """
        try:
            self._execute(cmd)
        except:
            pass

    @builder_method()
    def install_deps(self, reset=False, rabbitmq_secret=None):
        self.system.package.update()
        self.system.package.install(PACKAGES)
        j.builders.db.redis.install(reset=reset)
        j.builders.runtimes.nodejs.install(reset=reset)
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

        if not self._done_check("rabbitmq_server"):
            cmd = "service rabbitmq-server start"
            self._execute(cmd)
            self._done_set("rabbitmq_server")
        if not self._done_check("rabbitmq_user"):
            rabbitmq_secret = rabbitmq_secret or "PASSWORD_FOR_EVENTS"
            cmd_rabbitmq = f"""
            sudo rabbitmqctl add_user {TAIGA_USER} {rabbitmq_secret}
            sudo rabbitmqctl add_vhost {TAIGA_USER}
            sudo rabbitmqctl set_permissions -p {TAIGA_USER} {TAIGA_USER} ".*" ".*" ".*"
            """
            self._execute(cmd_rabbitmq)
            self._done_set("rabbitmq_user")

    @builder_method()
    def _backend_install(
        self, backend_repo="https://github.com/taigaio/taiga-back.git", rabbitmq_secret=None, branch="stable"
    ):
        rabbitmq_secret = rabbitmq_secret or "PASSWORD_FOR_EVENTS"
        j.clients.git.pullGitRepo(backend_repo, self.backend_repo_dir, branch=branch)
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
        self._write(
            f"{self.backend_repo_dir}/settings/local.py", MEDIA_CONF_FILE % {"PASSWORD_FOR_EVENTS": rabbitmq_secret}
        )

    @builder_method()
    def _frontend_install(
        self, frontend_repo="https://github.com/taigaio/taiga-front-dist.git", host=None, port=None, branch="stable"
    ):
        host = host or self.host
        port = port or self.port
        j.clients.git.pullGitRepo(frontend_repo, self.frontend_repo_dir, branch=branch)
        conf_dict = j.data.serializers.json.load(f"{self.frontend_repo_dir}/dist/conf.example.json")
        conf_dict["api"] = f"{self.protocol}://{host}:{port}/api/v1/"
        j.data.serializers.json.dump(f"{self.frontend_repo_dir}/dist/conf.json", conf_dict)

    @builder_method()
    def _events_install(
        self, events_repo="https://github.com/taigaio/taiga-events.git", rabbitmq_secret=None, branch="master"
    ):
        rabbitmq_secret = rabbitmq_secret or "PASSWORD_FOR_EVENTS"
        j.clients.git.pullGitRepo(events_repo, self.events_repo_dir, branch=branch)

        conf_dict = j.data.serializers.json.load(f"{self.events_repo_dir}/config.example.json")
        conf_dict["url"] = f"amqp://taiga:{rabbitmq_secret}@localhost:5672/taiga"
        conf_dict["secret"] = rabbitmq_secret
        j.data.serializers.json.dump(f"{self.events_repo_dir}/config.json", conf_dict)
        command = f"""
        chown -R {TAIGA_USER} {self.events_repo_dir}
        su - {TAIGA_USER} -c '
        export PATH=$PATH:{self.DIR_BIN}
        cd {self.events_repo_dir}
        npm install
        npm audit fix --force'
        npm install
        """
        self._execute(command)

    @builder_method()
    def install(self, reset=True):
        self.install_deps(reset=reset)
        self._backend_install()
        j.sal.fs.createDir(NGINX_LOG_DIR)
        self._frontend_install()
        self._events_install()

    # @builder_method()
    def start(self):
        self._write(
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

        taiga_events = j.servers.startupcmd.get("taiga_events")
        taiga_events.path = f"{self.events_repo_dir}"
        taiga_events.cmd_start = f"""
            su {self.TAIGA_USER} -c 'export PATH=$PATH:{self.DIR_BIN};cd {self.events_repo_dir}; /bin/bash -c \\"node_modules/coffeescript/bin/coffee index.coffee\\"'
            """
        return [taiga_events, taiga_server]
