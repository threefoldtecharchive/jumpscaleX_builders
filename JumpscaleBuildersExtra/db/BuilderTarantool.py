from Jumpscale import j


class BuilderTarantool(j.builders.system._BaseClass):
    def _init(self, **kwargs):
        self.git_url = "https://github.com/tarantool/tarantool.git"

    def install(self, reset=False, branch="2.1.1"):  # branch='1.10.1'
        """



        Install tarantool
        :param reset: reinstall if reset is True
        :param branch: the branch to install from
        :return:
        """
        if self._done_check("install", reset):
            return

        j.builders.buildenv.install()

        if j.core.platformtype.myplatform.platform_is_osx:
            # cmd="brew install tarantool"
            j.builders.system.package.ensure("lua,tarantool,luajit,cmake,msgpuck")

            C = """
            set -ex
            pushd {DIR_TEMP}
            git clone http://luajit.org/git/luajit-2.0.git
            cd luajit-2.0/
            git checkout v2.1
            make && sudo make install
            ln -sf /usr/local/bin/luajit-2.1.0-beta3 /usr/local/bin/luajit
            popd

            pushd {DIR_TEMP}
            git clone --recursive https://github.com/Sulverus/tdb
            cd tdb
            make
            sudo make install prefix=/usr//local/opt/tarantool

            sudo luarocks install redis-lua
            sudo luarocks install yaml
            sudo luarocks install penlight
            sudo luarocks install luasec OPENSSL_DIR=/usr//local/opt/openssl@1.1
            sudo tarantoolctl rocks install shard
            sudo tarantoolctl rocks install document
            sudo tarantoolctl rocks install prometheus
            sudo tarantoolctl rocks install queue
            sudo tarantoolctl rocks install expirationd
            sudo tarantoolctl rocks install connpool
            sudo tarantoolctl rocks install http


            # sudo luarocks install luatweetnacl

            sudo luarocks install lua-cjson

            popd
            """
            j.builders.tools.execute(C)
        elif j.core.platformtype.myplatform.platform_is_ubuntu:
            if not self._done_check("dependencies", reset):
                # j.builders.system.package.ensure('build-essential,cmake,coreutils,sed,libreadline-dev,'
                #                                    'libncurses5-dev,libyaml-dev,libssl-dev,libcurl4-openssl-dev,'
                #                                    'libunwind-dev,python,python-pip,python-setuptools,python-dev,'
                #                                    'python-msgpack,python-yaml,python-argparse,'
                #                                    'python-six,python-gevent,luarocks')

                # should be mainly done in j.builders.buildenv.install()
                j.builders.system.package.ensure(
                    "build-essential,cmake,coreutils,sed,libreadline-dev,"
                    "libncurses5-dev,libyaml-dev,libssl-dev,libcurl4-openssl-dev,"
                    "libunwind-dev,luarocks"
                )

                requirements = "https://raw.githubusercontent.com/tarantool/test-run/master/requirements.txt"
                download_to = "/tmp/tarantool_requirements.txt"
                j.builders.tools.file_download(requirements, to=download_to, minsizekb=0)
                cmd = "pip3 install -r %s" % download_to
                j.sal.process.execute(cmd, profile=True)

                self._done_set("dependencies")

            tarantool = "tarantool"
            if not self._done_check(tarantool, reset):
                j.builders.runtimes.build.build(
                    tarantool,
                    self.git_url,
                    branch=branch,
                    pre_build=["git submodule update --init --recursive"],
                    cmake=True,
                    cmake_args=["-DENABLE_DIST=ON"],
                    make=True,
                    make_install=True,
                )
                self._done_set(tarantool)

            luajit = "luajit"
            if not self._done_check(luajit, reset):
                repo = "http://luajit.org/git/luajit-2.0.git"
                post_build = ["ln -sf /usr/local/bin/luajit-2.1.0-beta3 /usr/local/bin/luajit"]
                j.builders.runtimes.build.build(
                    luajit, repo, branch="v2.1", make=True, make_install=True, post_build=post_build
                )
                self._done_set(luajit)

            tdb = "tdb"
            if not self._done_check(tdb, reset):
                repo = "https://github.com/Sulverus/tdb"
                j.builders.runtimes.build.build(
                    tdb, repo, pre_build=["git submodule update --init --recursive"], make=True, make_install=True
                )
                self._done_set(tdb)

            msgpuck = "msgpuck"
            if not self._done_check(msgpuck, reset):
                repo = "https://github.com/rtsisyk/msgpuck.git"
                j.builders.runtimes.build.build(msgpuck, repo, cmake=True, make=True, make_install=True)
                self._done_set("msgpuck")

            self._done_set("install")

    def install_luarocks_rock(self, name):
        """
        Installs a luarocks rock
        :param name: name of the rock to install
        :return:
        """

        if not self._done_check("install"):
            raise Exception("Tarantool is not installed")

        command = """
            set -ex
            pushd /tmp
            luarocks install {name}
            popd
            """.format(
            name=name
        )
        j.builders.tools.execute(command)

    def install_tarantool_rock(self, name):
        """
        Installs a tarantool rock
        :param name: name of the rock to install
        :return:
        """
        if not self._done_check("install"):
            raise Exception("Tarantool is not installed")
        command = """
        set -ex
        pushd /tmp
        tarantoolctl rocks install {name}
        popd
        """.format(
            name=name
        )
        j.builders.tools.execute(command)

    def start(self, port=3301, passwd="admin007"):
        """
        Start tarantool in a tmux
        """
        prefab = self.prefab

        LUA = """
        box.cfg{listen = $port}
        box.schema.user.create('admin', {if_not_exists = true,password = '$passwd'})
        box.schema.user.passwd('admin','$passwd')
        require('console').start()
        """
        LUA = LUA.replace("$passwd", passwd)
        LUA = LUA.replace("$port", str(port))

        luapath = tools.replace("{DIR_TEMP}/tarantool.lua")

        self._log_info("write lua startup to:%s" % luapath)

        tools.file_write(luapath, LUA)

        cmd = "cd {DIR_TEMP};rm -rf tarantool;mkdir tarantool;cd tarantool;tarantool %s" % luapath
        pm = j.builders.system.processmanager.get()
        pm.ensure(name="tarantool", cmd=cmd, env={}, path="")

        # RESULT IS RUNNING TARANTOOL IN TMUX
