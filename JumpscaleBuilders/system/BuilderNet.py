import re
from Jumpscale import j


class BuilderNet(j.baseclasses.builder):
    def tcpport_check(self, port, prefix=""):
        res = []
        for item in self.info_get(prefix):
            if item["localport"] == port:
                return True
        return False

    def info_get(self):
        """
        return
        [$item,]

        $item is dict

        {'local': '0.0.0.0',
         'localport': 6379,
         'pid': 13824,
         'process': 'redis',
         'receive': 0,
         'receivebytes': 0,
         'remote': '0.0.0.0',
         'remoteport': '*',
         'send': 0,
         'sendbytes': 0,
         'parentpid':0}


        """
        result = []
        if "linux" in j.core.platformtype.myplatform.platformtypes:
            cmdlinux = "netstat -lntp"
            _, out, _ = j.sal.process.execute(cmdlinux, showout=False)
            # to troubleshoot https://regex101.com/#python
            p = re.compile(
                "tcp *(?P<receive>[0-9]*) *(?P<send>[0-9]*) *(?P<local>[0-9*.]*):(?P<localport>[0-9*]*) *(?P<remote>[0-9.*]*):(?P<remoteport>[0-9*]*) *(?P<state>[A-Z]*) *(?P<pid>[0-9]*)/(?P<process>\w*)"
            )
            for line in out.split("\n"):
                res = re.search(p, line)
                if res is not None:
                    # self._log_info(line)
                    d = res.groupdict()
                    d["process"] = d["process"].lower()
                    if d["state"] == "LISTEN":
                        d.pop("state")
                        result.append(d)
            # now tcp6
            p = re.compile(
                "tcp6 *(?P<receive>[0-9]*) *(?P<send>[0-9]*) *(?P<local>[0-9*.:]*):(?P<localport>[0-9*]*) *(?P<remote>[0-9.*:]*):(?P<remoteport>[0-9*]*) *(?P<state>[A-Z]*) *(?P<pid>[0-9]*)/(?P<process>\w*)"
            )
            for line in out.split("\n"):
                res = re.search(p, line)
                if res is not None:
                    # self._log_info(line)
                    d = res.groupdict()
                    d["process"] = d["process"].lower()
                    if d["state"] == "LISTEN":
                        d.pop("state")
                        result.append(d)

        elif "darwin" in j.core.platformtype.myplatform.platformtypes:
            # cmd='sudo netstat -anp tcp'
            # # out=j.sal.process.execute(cmd)
            # p = re.compile(u"tcp4 *(?P<rec>[0-9]*) *(?P<send>[0-9]*) *(?P<local>[0-9.*]*) *(?P<remote>[0-9.*]*) *LISTEN")
            cmd = "lsof -i 4tcp -sTCP:LISTEN -FpcRn"
            _, out, _ = j.sal.process.execute(cmd, showout=False)
            d = {}
            for line in out.split("\n"):
                if line.startswith("p"):
                    d = {
                        "local": "",
                        "localport": 0,
                        "pid": 0,
                        "process": "",
                        "receive": 0,
                        "receivebytes": 0,
                        "remote": "",
                        "remoteport": 0,
                        "send": 0,
                        "sendbytes": 0,
                        "parentpid": 0,
                    }
                    d["pid"] = int(line[1:])
                if line.startswith("R"):
                    d["parentpid"] = int(line[1:])
                if line.startswith("c"):
                    d["process"] = line[1:].strip()
                if line.startswith("n"):
                    a, b = line.split(":")
                    d["local"] = a[1:].strip()
                    try:
                        d["localport"] = int(b)
                    except BaseException:
                        d["localport"] = 0
                    result.append(d)

        else:
            raise j.exceptions.RuntimeError("platform not supported")

        for d in result:
            for item in ["receive", "send", "pid", "localport", "remoteport"]:
                if d[item] == "*":
                    continue
                else:
                    d[item] = int(d[item])

        return result
