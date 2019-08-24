import pytest
from Jumpscale import j


@pytest.mark.integration
def test_main(self=None):
    """test openResty installation

    to run:
    kosmos 'j.builders.web.openresty._test(name="openResty")'
    """

    if not j.sal.process.checkInstalled(j.builders.web.openresty.NAME):
        # j.builders.web.openresty.stop()
        # openresty is built with lapis in lua builder
        j.builders.runtimes.lua.build(reset=True)
        j.builders.runtimes.lua.install()

    # try to start/stop lapis with lua
    tmux_pane = j.builders.web.openresty.start()
    tmux_process = tmux_pane.process_obj
    child_process = tmux_pane.process_obj_child
    assert child_process.is_running()
    assert j.sal.nettools.waitConnectionTest("localhost", 8080)
