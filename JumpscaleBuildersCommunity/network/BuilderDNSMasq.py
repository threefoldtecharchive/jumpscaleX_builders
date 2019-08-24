from Jumpscale import j


from JumpscaleLib.sal.dnsmasq.Dnsmasq import DNSMasq


class BuilderDNSMasq(base, DNSMasq):
    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
