

<img src="./static-assets/DynamicRoutingUpdater.svg" alt="drawing" width="200"/>
<br>
<p>┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻ </p>
<br>

# Dynamic Routing-table updater (DRU)

Example of reference.json
```json
{
    "tableName": "direct",
    "adapter": [
        "enp1s0f0",
        "enp1s0f1"
    ]
}
```
`tableName` will be the table name the program will use to direct routes and rules against </br>
```adapter``` will be the interfaces you will split out from the main routing table</br>

When you or the service starts up DRU,
it will prepare the required data. <br>
After the data has been loaded, it will be ready to start. All this occurs within the init call.

When DRU gets the start call, it will do the following:
- Remove old DRU tables (based on the Table name passed)
- Find all occupied table ids
- Filter out occupied
- Define table id and name for all network adapters added
- Write the newly filtered and appended routing table

After DRU has started, and processed the routing table, it will start up DRUHook. <br>
This is a sub component of DRU, which is intended to watch the network interfaces assigned to DRU and perform routing changes on them.<br>

If you want to test DRU out, you can do the following
```python

from DynamicRoutingUpdater import DynamicRoutingUpdater
service = DynamicRoutingUpdater()
service.dryrun()

```
<strong style="color: red">NOTE!</strong> This <strong>WILL</strong> do modifications to your routing table! <br>
This will also change and modify your current routes, and <strong>WILL NOT BE RESTORED!</strong>

Usually a reboot is enough to get it recreated, as the code does not include persistance

# How to install
## Dependencies
```shell
net-tools
```


To install and start DRU
- Clone the project 
- Modify reference.json
 - `./install.sh` 

</br>
Make sure that you run the script with sudo or as root, as the script needs access. <br>

Or you can do the following:
```shell
curl -sSL -o install.sh https://raw.githubusercontent.com/bskjon/DynamicRoutingUpdater/master/install.sh && sudo bash install.sh
```
This will request you to define table name and select interface thrould selection.


<br>
A copy of your routing table will exist as:

```sh
/etc/iproute2/rt_tables.bak
```
