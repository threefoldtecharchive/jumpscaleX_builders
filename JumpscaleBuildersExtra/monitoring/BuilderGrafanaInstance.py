from Jumpscale import j

# servers only run on ubuntu 18.04


class GrafanaComponent(j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.builder.grafana.1
        name* = "" (S)
        addr = "" (S)
        port = 7777 (I)
        secret = "" (S)
        """

    def _init(self, **kwargs):
        pass

    def start(self):
        self.cache.delete("stop")  # make sure that we will redo the stop action

        def do():
            pass
            # implement the logic how to start, use tmux

        if not self.running(refresh=True, timeout=0):
            self.cache.get(key="start", method=do, refresh=True, die=True)
        assert self.running() == True

    def stop(self):
        """
        stop the server and test that the server was stopped
        :return:
        """
        self.cache.delete("start")  # make sure that we will redo the stop action
        self.cache.delete("running")

        def do():
            pass
            # implement the logic how to start, use tmux, can be forced if gracful does not work
            # do a graceful shutdown first !!!

        self.cache.get(key="stop", method=do, refresh=True, die=True)
        assert self.running() == False

    def running(self, timeout=60, refresh=True):
        """
        check server is running, there is a std timeout when 0 will only do 1 check
        best to implement using our caching framework
        :return:
        """

        def do():
            pass
            # implement the logic how to start, use tmux

        self.cache.get(key="running", method=do, timeout=timeout, refresh=refresh, expire=10, die=True)
        # expiration 0 means will always check again, sometimes makes sense to not recheck e.g. in 5 sec
        # refresh can be overruled so will check everytime (only relevant to use when expire is not 0)

        pass

    def reset(self):
        """
        remove all data
        :return:
        """
        self.cache.reset()  # all cached states need to go
        # TODO:

        pass

    def test(self):
        pass
        # do a basic test, look for client
        # make connection
        # some test

    @property
    def client(self):
        # return the client using j.clients.... using arguments from this server
        pass
