import textwrap

from Jumpscale import j

builder_method = j.baseclasses.builder_method

# /tmp is the default directory for postgres unix socket
SIMPLE_CFG = """
[options]
admin_passwd = rooter
db_host = localhost
db_user = root"""


class BuilderOdoo(j.baseclasses.builder):
    __jslocation__ = "j.builders.apps.odoo"

    def _init(self, **kwargs):
        self.VERSION = "12.0"
        self.dbname = None
        self.intialize = False
        self.APP_DIR = self._replace("{DIR_BASE}/apps/odoo")

    @builder_method()
    def configure(self):
        pass

    @builder_method()
    def install(self, reset=False):
        """
        kosmos 'j.builders.apps.odoo.install()'
        kosmos 'j.builders.apps.odoo.start()'
        install odoo
        """
        j.builders.db.psql.install(reset=reset)
        j.builders.runtimes.nodejs.install(reset=reset)

        self.tools.dir_ensure(self.APP_DIR)

        j.builders.system.package.install(
            "sudo libxml2-dev libxslt1-dev libsasl2-dev python3-dev libldap2-dev libssl-dev python3-pypdf2 python3-passlib python3-lxml python3-reportlab python3-dateutil"
        )  # create user and related config
        j.builders.runtimes.python3.pip_package_install(["pytz", "jinja2", "MarkupSafe", "html2text"])
        self._execute(
            """
            id -u odoouser &>/dev/null || (useradd odoouser --home {APP_DIR} --no-create-home --shell /bin/bash
            sudo su - postgres -c "/sandbox/bin/createuser -s odoouser") || true
            mkdir -p {APP_DIR}/data
            chown -R odoouser:odoouser {APP_DIR}
            sudo -H -u odoouser /sandbox/bin/initdb -D {APP_DIR}/data || true
        """
        )

        self._execute(
            """
        cd {APP_DIR}

        if [ ! -d odoo/.git ]; then
            git clone https://github.com/odoo/odoo.git -b {VERSION} --depth=1
        fi

        cd odoo
        # sudo -H -u odoouser python3 -m pip install --user -r requirements.txt
        python3 setup.py  install
        chmod +x odoo-bin
        """
        )

        j.builders.runtimes.nodejs.npm_install("rtlcss")

        print("INSTALLED OK, PLEASE GO TO http://localhost:8069")
        # print("INSTALLED OK, PLEASE GO TO http://localhost:8069/web/database/selector")

    def start(self):
        """
        kosmos 'j.builders.apps.odoo.start()'
        :return:
        """
        if not j.builders.db.psql.running():
            j.builders.db.psql.start()

        cl = j.clients.postgres.db_client_get()
        self._write("{DIR_CFG}/odoo.conf", SIMPLE_CFG)

        j.servers.odoo.default.start()
        print("INSTALLED OK, PLEASE GO TO http://localhost:8069    masterpasswd:rooter")

    def set_dbname(self, name):
        self.dbname = name

    def stop(self):
        """
        kosmos 'j.builders.apps.odoo.stop()'
        :return:
        """
        j.servers.odoo.default.stop()
