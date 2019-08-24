# Filemanager

Filemanager is a caddy build with [iyo authentication](https://github.com/itsyouonline/caddy-integration) and [filebrowser](https://github.com/filebrowser/caddy) plugins.


## Run on zos
To run file manager on zos, you can use this flist here [here](https://hub.grid.tf/abdelrahman/filemanager.flist.md) or you can [build your own](#Build-filemanager-flist).


A container should be created with the following environment variables:

* node_addr: zero-os node address
* filemanager_port
* iyo_client_id: your [itsyou.online](https://itsyou.online) client id
* iyo_client_secret: your [itsyou.online](https://itsyou.online) client secret

See [how to get a client id and secret from itsyou.online](iyo_api_key.md)

for example using zero-os [python client](https://github.com/threefoldtech/0-core/blob/development/docs/interacting/python.md):

```python
from zeroos.core0.client import Client

node_addr = 'your_node_ip_address'
port = 5081

cl = Client(node_addr)
cl.container.create(
    'https://hub.grid.tf/abdelrahman/filemanager.flist',
    port={port: port},
    env={
        'node_addr': node_addr,
        'filemanager_port': str(port),
        'iyo_client_id': 'your_iyo_client_id',
        'iyo_client_secret': 'your_iyo_client_secret'
    }
).get()
```

if the container is created, you should be able to access filemanager on `http://<your_node_ip_address>:5081`.

## Build filemanager flist
to build caddy with itsyouonline and filemanager plugins

`j.builders.web.filemanager.build()`

to create and publish your flist

`j.builders.web.filemanager.flist_create('your_hub_instance')`
