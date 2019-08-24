import pytest
from Jumpscale import j


@pytest.mark.integration
def test_main(self=None):
    """test traefik installation

    to run:
    kosmos 'j.builders.web.traefik._test(name="traefik")'
    """

    if not j.sal.process.checkInstalled(j.builders.web.traefik.NAME):
        j.builders.web.traefik.install(reset=True)

    # try to start/stop
    tmux_pane = j.builders.web.traefik.start()
    tmux_process = tmux_pane.process_obj
    child_process = tmux_pane.process_obj_child
    assert child_process.is_running()
    j.builders.web.traefik.stop(tmux_process.pid)
