from Jumpscale import j


class BuilderBlockchainFactory(j.builders.system._BaseFactoryClass):

    __jslocation__ = "j.builders.blockchain"

    def _init(self, **kwargs):
        self._tfchain = None
        self._ethereum = None
        self._bitcoin = None
        self._ripple = None

    @property
    def tfchain(self):
        if self._tfchain is None:
            from .BuilderTFChain import BuilderTFChain

            self._tfchain = BuilderTFChain()
        return self._tfchain

    @property
    def ethereum(self):
        if self._ethereum is None:
            from .BuilderEthereum import BuilderEthereum

            self._ethereum = BuilderEthereum()
        return self._ethereum

    @property
    def bitcoin(self):
        if self._bitcoin is None:
            from .BuilderBitcoin import BuilderBitcoin

            self._bitcoin = BuilderBitcoin()
        return self._bitcoin

    @property
    def ripple(self):
        if self._ripple is None:
            from .BuilderRipple import BuilderRipple

            self._ripple = BuilderRipple()
        return self._ripple
