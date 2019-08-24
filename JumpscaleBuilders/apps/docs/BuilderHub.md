# 0-hub builder
### Allow people to create their own hub: create flist + launch script which launches container who has everything which hub has so people can use this to develop full life cycle management

## Install locally

```python 
export IP_PORT="127.0.0.1:5555"
```
* or export your IP in kosmos via  `>>> j.builders.apps.hub.in_docker("127.0.0.1:5555")`
### Using kosmos
```
j.builders.apps.hub.install()
```

## Start locally
### Using kosmos
```
j.builders.apps.hub.start()
```
You can view it 

``` your-host-ip:5555```


## Install in container
### Create flist 
Using kosmos 
```
j.builders.apps.hub.sandbox(zhub_client=your_zhub_cleint, flist_create=True, reset=True) 
```

**Then merge this flist with JSX flist :**

**Base on** : your flist

**merge with** : ```https://hub.grid.tf/tf-autobuilder/threefoldtech-jumpscaleX-autostart-development.flist```

## Create container :

Using kosmos

```
cl =j.clients.zos.get("zhub", host="IP_Node", password=jwt)


cl.client.container.create(name='testzhub',root_url='your_flist_after_merge',nics=[{'type':'default', 'name':'defaultnic', 'id':' None'}], port{2015:2015,8080:80, 5555:5555}, env={"IP_PORT":"IP_Node:5555"}).get()
```

You can view it 

```IP_Node:5555```<br>
example ```10.102.178.130:5555```