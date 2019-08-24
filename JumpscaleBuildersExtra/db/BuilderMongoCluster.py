from Jumpscale import j
from time import sleep


class Startable:
    """
    This class to ensure that things get installed and started only once
    """

    def _install(self):
        self.installed = True

    def _start(self):
        self.started = True

    def install(self, *args, **kwargs):
        if not self.installed:
            return self._install()
        else:
            return False

    def start(self, *args, **kwargs):
        if not self.started:
            return self._start()
        else:
            return False

    @staticmethod
    def ensure_started(fn):
        def fn2(self, *args, **kwargs):
            if not self.started:
                self.start()
            return fn(self, *args, **kwargs)

        return fn2

    @staticmethod
    def ensure_installed(fn):
        def fn2(self, *args, **kwargs):
            if not self.installed:
                self.install()
            return fn(self, *args, **kwargs)

        return fn2


class MongoInstance(Startable):
    """
    This class represents a mongo instance
    """

    def __init__(
        self,
        prefab,
        addr=None,
        private_port=27021,
        public_port=None,
        type_="shard",
        replica="",
        configdb="",
        dbdir=None,
    ):
        super().__init__()
        self.prefab = prefab
        if not addr:
            self.addr = prefab.executor.addr
        else:
            self.addr = addr
        self.private_port = private_port
        self.public_port = public_port
        self.type_ = type_
        self.replica = replica
        self.configdb = configdb
        if dbdir is None:
            dbdir = "{DIR_VAR}/data/db"
        if public_port is None:
            public_port = private_port
        self.dbdir = dbdir
        self._log_info(prefab, private_port, public_port, type_, replica, configdb, dbdir)

    def _install(self):
        super()._install()
        j.core.tools.dir_ensure(self.dbdir)
        return j.builders.apps.mongodb.build(start=False)

    def _gen_service_name(self):
        name = "ourmongos" if self.type_ == "mongos" else "ourmongod"
        if self.type_ == "cfg":
            name += "_cfg"
        return name

    def _gen_service_cmd(self):
        cmd = "mongos" if self.type_ == "mongos" else "mongod"
        args = ""
        if self.type_ == "cfg":
            args += " --configsvr"
        if self.type_ != "mongos":
            args += " --dbpath %s" % (self.dbdir)
        if self.private_port:
            args += " --port %s" % (self.private_port)
        if self.replica:
            args += " --replSet %s" % (self.replica)
        if self.configdb:
            args += " --configdb %s" % (self.configdb)
        return "{DIR_BIN}/" + cmd + args

    @Startable.ensure_installed
    def _start(self):
        super()._start()
        self._log_info("starting: ", self._gen_service_name(), self._gen_service_cmd())
        pm = j.builders.system.processmanager.get()
        pm.ensure(self._gen_service_name(), self._gen_service_cmd())
        return a

    @Startable.ensure_started
    def execute(self, cmd):
        for i in range(5):
            rc, out, err = j.sal.process.execute(
                "LC_ALL=C {DIR_BIN}/mongo --port %s --eval '%s'"
                % (self.private_port, cmd.replace("\\", "\\\\").replace("'", "\\'")),
                die=False,
            )
            if not rc and out.find("errmsg") == -1:
                self._log_info("command executed %s" % (cmd))
                break
            sleep(5)
        else:
            self._log_info("cannot execute command %s" % (cmd))
        return rc, out

    def __repr__(self):
        return "%s:%s" % (self.addr, self.public_port)

    __str__ = __repr__


class MongoSInstance(Startable):
    """
    This class represents a mongos instance
    """

    def __init__(self, nodes, configdb):
        super().__init__()
        self.nodes = nodes
        self.configdb = configdb
        for i in nodes:
            i.configdb = configdb
            i.type_ = "mongos"

    @Startable.ensure_installed
    def _start(self):
        super()._start()
        self.configdb.start()
        [i.start() for i in self.nodes]

    @Startable.ensure_started
    def add_shard(self, replica):
        self.nodes[0].execute('sh.addShard( "%s" )' % (replica))

    def add_shards(self, replicas):
        return [self.add_shard(i) for i in replicas]


class MongoCluster(Startable):
    """
    This class represents the cluster itself
    """

    def __init__(self, nodes, configdb, shards, unique=""):
        super().__init__()
        self.nodes = nodes
        self.configdb = configdb
        self.shards = shards
        self.unique = unique
        self.mongos = MongoSInstance(nodes, configdb)

    def add_shards(self):
        self.mongos.add_shards(self.shards)

    def _install(self):
        super()._install()
        [i.install() for i in self.shards]
        self.mongos.start()
        self.add_shards()

    @Startable.ensure_installed
    def _start(self):
        super()._start()
        self.mongos.start()
        [i.start() for i in self.shards]


class MongoReplica(Startable):
    """
    This class represents a replica set
    """

    def __init__(self, nodes, primary=None, name="", configsvr=False):
        super().__init__()
        if not primary:
            primary = nodes[0]
            nodes = nodes[1:]

        self.name = name
        self.configsvr = configsvr
        self.primary = primary
        self.nodes = nodes
        self.all = [primary] + nodes

        for i in self.all:
            i.replica = name
            if configsvr:
                i.type_ = "cfg"

    def _prepare_json_all(self):
        reprs = [repr(i) for i in self.all]
        return ", ".join(['{ _id: %s, host: "%s" , priority: %f}' % (i, k, 1.0 / (i + 1)) for i, k in enumerate(reprs)])

    def _prepare_init(self, **kwargs):
        cfg = "configsvr: true,version:1," if self.configsvr else ""
        return """rs.initiate( {_id: "%s",%smembers: [%s]} )""" % (self.name, cfg, self._prepare_json_all())

    def _install(self):
        super()._install()
        self.start()
        self.primary.execute(self._prepare_init())

    @Startable.ensure_installed
    def _start(self):
        super()._start()
        for i in self.all:
            i.start()

    def __repr__(self):
        return "%s/%s" % (self.name, self.primary)

    __str__ = __repr__


class MongoConfigSvr(Startable):
    """
    This class represents the config server
    """

    def __init__(self, nodes, primary=None, name=""):
        super().__init__()
        self.name = name
        self.rep = MongoReplica(nodes, primary, name=self.name, configsvr=True)

    @Startable.ensure_installed
    def _start(self):
        super()._start()
        self.rep.start()

    def __repr__(self):
        return self.rep.__repr__()

    __str__ = __repr__


class BuilderMongoCluster(j.builders.system._BaseClass):
    def mongoCluster(self, shards_nodes, config_nodes, mongos_nodes, shards_replica_set_counts=1):
        """
        shards_nodes: a list of executors of the shards
        config_nodes: a list of executors of the config servers
        mongos_nodes: a list of executors of the mongos instanses
        shards_replica_set_count: the number of nodes in a replica set in the shards
        you can find more info here https://docs.mongodb.com/manual/tutorial/deploy-shard-cluster/
        """

        def construct_dict(node):
            return {"executor": node, "private_port": 27017, "public_port": 27017, "dbdir": None}

        return self._mongoCluster(
            map(construct_dict, shards_nodes),
            map(construct_dict, config_nodes),
            map(construct_dict, mongos_nodes),
            shards_replica_set_counts,
        )

    def _mongoCluster(self, shards_nodes, config_nodes, mongos_nodes, shards_replica_set_counts=1, unique=""):
        args = []
        for i in [shards_nodes, config_nodes, mongos_nodes]:
            prefabs = []
            for k in i:
                prefabs.append(
                    MongoInstance(
                        j.tools.prefab.get(k["executor"]),
                        addr=k.get("addr", None),
                        private_port=k["private_port"],
                        public_port=k.get("public_port"),
                        dbdir=k.get("dbdir"),
                    )
                )
            args.append(prefabs)
        return self.__mongoCluster(
            args[0], args[1], args[2], shards_replica_set_counts=shards_replica_set_counts, unique=unique
        )

    def __mongoCluster(self, shards_css, config_css, mongos_css, shards_replica_set_counts=1, unique=""):
        shards_replicas = [
            shards_css[i : i + shards_replica_set_counts] for i in range(0, len(shards_css), shards_replica_set_counts)
        ]
        shards = [MongoReplica(i, name="%s_sh_%d" % (unique, num)) for num, i in enumerate(shards_replicas)]
        cfg = MongoConfigSvr(config_css, name="%s_cfg" % (unique))
        cluster = MongoCluster(mongos_css, cfg, shards)
        cluster.install()
        cluster.start()
        return cluster

    def createCluster(self, executors, numbers=None):
        """
        @param executors

        e.g.
        e1=j.tools.executor.getSSHBased(addr="10.0.3.65", port=22, login="root", passwd="rooter")
        e2=j.tools.executor.getSSHBased(addr="10.0.3.254", port=22, login="root", passwd="rooter")
        e3=j.tools.executor.getSSHBased(addr="10.0.3.194", port=22, login="root", passwd="rooter")
        executors=[e1,e2,e3]

        @param numbers
        a tuple containing the number of shards, config servers, mongos instances
        and nodes per shards' replica set
        >>> numbers=(4, 2, 1, 2)
        means 4 hards with two replica sets, 2 config servers, 1 mongos instance
        if not passed it will be (len(executors) - 2, 1, 1, 1)
        """

        numbers = numbers or (len(executors) - 2, 1, 1, 1)

        return self.mongoCluster(
            executors[: numbers[0]],
            executors[numbers[0] : numbers[0] + numbers[1]],
            executors[numbers[0] + numbers[1] : numbers[0] + numbers[1] + numbers[2]],
            numbers[3],
        )
