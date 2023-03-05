#!/bin/sh

echo "Backuping rt_tables"

if [ -f "/etc/iproute2/rt_tables.bak" ]; then
    echo "rt_tables.bak already exists"
else
    cp /etc/iproute2/rt_tables /etc/iproute2/rt_tables.bak
fi

sudo apt install -y python3-pip

echo "Installing dependencies"
pip install pyDynamicRoutingUpdater -U

systemctl stop dynamic-routing-updater.service
systemctl disable dynamic-routing-updater.service

rm /etc/systemd/system/dynamic-routing-updater.service

systemctl daemon-reload

mkdir --parents /usr/local/dynamic-routing-updater/

echo "Creating DRU Service runner"
cat > /usr/local/dynamic-routing-updater/service.py <<EOL
from DynamicRoutingUpdater import DynamicRoutingUpdater
reference = "reference.json"
service = DynamicRoutingUpdater()
service.start()
EOL

cp ./reference.json /usr/local/dynamic-routing-updater/reference.json
referenceAbsPath="/usr/local/dynamic-routing-updater/reference.json"
sed -i "s^reference.json^$referenceAbsPath^g" /usr/local/dynamic-routing-updater/service.py

echo "Creating DIPWA"
tee > (cat > /etc/networkd-dispatcher/routable.d/dipwa.sh) > (cat > /usr/lib/networkd-dispatcher/routable.d/dipwa.sh)  <<EOL
#!/bin/sh

# Dynamic Ip Watcher Action (DIPWA)
# A component of DynamicRoutingUpdater
# 
# The purpose of Dipwa is to be notified by the system when there are changes to net network interface
# If this script is placed correctly inside a hook folder for the network manager, 
# the network manager will call up this script whith the interface that has been updated or altered
#
# This script will then proceed to update a temporary file which the service DRU will watch and respond to
#

echo "DynamicIpWatcherAction: Registered change to network adpater $IFACE"

if [ ! -z $IFACE ]
then
    echo $IFACE > /tmp/dipwa
fi
EOL

echo "Creating DRU Service"
cat > /etc/systemd/system/dynamic-routing-updater.service <<EOL
[Unit]
Description=Dynamic Routing Updater - Table flipper

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python3 -u /usr/local/dynamic-routing-updater/service.py
Environment=PYTHONUNBUFFERED=1


[Install]
WantedBy=multi-user.target
EOL

chmod 700 /etc/networkd-dispatcher/routable.d/dipwa.sh
chmod 700 /usr/lib/networkd-dispatcher/routable.d/dipwa.sh

chmod +x /etc/networkd-dispatcher/routable.d/dipwa.sh
chmod +x /usr/lib/networkd-dispatcher/routable.d/dipwa.sh


chmod 700 /usr/local/dynamic-routing-updater/service.py
chmod +x /usr/local/dynamic-routing-updater/service.py

chown root:root /usr/local/dynamic-routing-updater/service.py

systemctl daemon-reload

systemctl enable dynamic-routing-updater.service
systemctl start dynamic-routing-updater.service

systemctl status dynamic-routing-updater.service

echo "Done!"