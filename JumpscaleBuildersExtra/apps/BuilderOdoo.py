import textwrap

from Jumpscale import j

builder_method = j.builders.system.builder_method

# /tmp is the default directory for postgres unix socket
SIMPLE_CFG = """
[options]
admin_passwd = rooter
db_host = localhost
db_user = root"""


class BuilderOdoo(j.builders.system._BaseClass):
    NAME = "odoo"

    def _init(self, **kwargs):
        self.VERSION = "12.0"
        self.dbname = None
        self.intialize = False
        self.APP_DIR = self._replace("{DIR_BASE}/apps/odoo")

    @builder_method()
    def configure(self):
        pass

    @builder_method()
    def install(self):
        """
        kosmos 'j.builders.apps.odoo.install()'
        kosmos 'j.builders.apps.odoo.start()'
        install odoo
        """
        j.builders.db.postgres.install(reset=True)
        j.builders.runtimes.nodejs.install(reset=True)

        self.tools.dir_ensure(self.APP_DIR)

        j.builders.system.package.install(
            "sudo libxml2-dev libxslt1-dev libsasl2-dev python3-dev libldap2-dev libssl-dev python3-pypdf2 python3-passlib python3-lxml python3-reportlab"
        )  # create user and related config
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
        j.builders.db.postgres.start()
        cl = j.clients.postgres.db_client_get()
        self._write("{DIR_CFG}/odoo.conf", SIMPLE_CFG)
        self.startup_cmds.start()
        print("INSTALLED OK, PLEASE GO TO http://localhost:8069    masterpasswd:rooter")

    def stop(self):
        j.builders.db.postgres.stop()
        self.startup_cmds.stop()

    def set_dbname(self, name):
        self.dbname = name

    @property
    def startup_cmds(self):
        """
        j.builders.apps.odoo.startup_cmds
        :return:
        """

        # odoo_start = self._replace(
        #     "sudo -H -u odoouser python3 /sandbox/apps/odoo/odoo/odoo-bin -c {DIR_CFG}/odoo.conf"
        # )
        if not self.dbname:
            raise j.exceptions.Value("invalid DB Name, use set_dbname with the correct database")

        search = j.sal.process.execute(
            """psql -h localhost -U postgres \
                --command="SELECT * FROM initialize_table WHERE available = 'yes';" """
        )
        if int(search[1].split("\n")[-3].split(" ")[0].split("(")[1]) > 0:
            odoo_start = self._replace(
                "sudo -H -u odoouser python3 /sandbox/apps/odoo/odoo/odoo-bin -c {DIR_CFG}/odoo.conf"
            )
        else:
            odoo_start = self._replace(
                "sudo -H -u odoouser python3 /sandbox/apps/odoo/odoo/odoo-bin -c {DIR_CFG}/odoo.conf -d %s -i base"
                % self.dbname
            )

            j.sal.process.execute(
                """psql -h localhost -U postgres \
                --command='INSERT INTO initialize_table (available) VALUES (TRUE);' """
            )

        odoo_cmd = j.servers.startupcmd.get("odoo")
        odoo_cmd.cmd_start = odoo_start
        odoo_cmd.process_strings = "/sandbox/apps/odoo/odoo/odoo-bin -c"
        odoo_cmd.path = "/sandbox/bin"
        odoo_cmd.ports = [8069]
        return odoo_cmd
