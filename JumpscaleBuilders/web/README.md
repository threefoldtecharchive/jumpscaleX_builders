## How to use jumpscaleX builders
### Builder functions
- `build`:
    - downloads & dependancies required for build
    - builds from source code
    - files should be in self.DIR_BUILD <br/>
    `example for coredns: j.builders.network.coredns.build()` <br/>
    - parameters:
        * reset=True > resets the build operation -calls reset method-

- `install`:
    - calls build at first
    - copies binaries & libs & any other related files to its correct location
    - makes configurations if required
    `example for coredns: j.builders.network.coredns.install()` <br/>
    - parameters:
        * reset=True > resets the build & install operation -calls reset method-

- `start`:
    - uses startupcmd(s) to start the server(s) or daemon(s) <br>
    `example usage: j.builders.network.coredns.start()`

- `stop`:
    - uses startupcmd(s) to stop the server(s) or daemon(s) <br>
    `example usage: j.builders.network.coredns.stop()`

- `reset`:
    - deletes all files in build directory and sandbox directory <br/>
     `example usage: j.builders.network.coredns.reset()`

- `test`:
    - Basic tests for the builder to make sure it's correctly working; aka: start server if available; do some operations on it; stops it.
    `example usage: j.builders.network.coredns.test()`

- `sandbox`:
    - calls build & install at first
    - copies required files (binaries, libraries and includes ...) and configurations to self.SANDBOX_DIR in correct locations 
    - then these files used to make a .tar file which is uploaded to the hub to make an flist.
    - if server needs to be autostart or needs configurations on init in the container it's done in a startup.toml and localized at the root of the flist

    - Main Parameters:
        - zhub_client > authenticated zhub object uploads files to https://hub.grid.tf.
            - how to get one:
                ```
                zhub = j.clients.zhub.myclient
                zhub.token_ = j.clients.itsyouonline.myclient.jwt_get().jwt
                and enter your itsyouonline id and secret
                zhub.authenticate()
                ```
                P.S: needs zeroos python package to be installed from: <br>
                `pip3 install -e 'git+https://github.com/threefoldtech/0-hub#egg=zerohub&subdirectory=client'`
        - flist_create > BOOL: create flist and upload it to the hub
        - param create_flist > BOOL: create flist after copying files
        - merge_base_flist > STR: if you want to merge your flist with another one, usually we use "tf-autobuilder/threefoldtech-jumpscaleX-development.flist"<br/>
    - Example of usage:
    ```
    j.builders.network.coredns.sandbox(
        zhub_client=zhub,
        flist_create=True,
        merge_base_flist="tf-autobuilder/threefoldtech-jumpscaleX-development.flist",
    ):
    ```