#!/bin/sh

echo "Backuping rt_tables"

if [ -f "/etc/iproute2/rt_tables.bak" ]; then
    echo "rt_tables.bak already exists"
else
    cp /etc/iproute2/rt_tables /etc/iproute2/rt_tables.bak
fi

chmod +x dipwa.sh
chmod +x service.py

sudo apt install -y python3-pip

echo "Installing dependencies"
pip install netaddr -U
pip install prompt_toolkit==1.0.14
pip install whaaaaat
pip install pyroute2

systemctl stop dip-table-flipper.service
systemctl disable dip-table-flipper.service


rm /etc/systemd/system/dip-table-flipper.service
rm /tmp/dipwa
rm -r /usr/local/dip-table-flipper


systemctl stop dynamic-routing-updater.service
systemctl disable dynamic-routing-updater.service

rm /etc/systemd/system/dynamic-routing-updater.service

systemctl daemon-reload

sleep 10s

mkdir --parents /usr/local/dynamic-routing-updater/
cp ./service.py /usr/local/dynamic-routing-updater/service.py
cp ./reference.json /usr/local/dynamic-routing-updater/reference.json
cp ./dipwa.sh /etc/networkd-dispatcher/routable.d/dipwa.sh
cp ./dipwa.sh /usr/lib/networkd-dispatcher/routable.d/dipwa.sh

referenceAbsPath="/usr/local/dynamic-routing-updater/reference.json"
sed -i "s^reference.json^$referenceAbsPath^g" /usr/local/dynamic-routing-updater/service.py


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

chmod 700 /usr/local/dynamic-routing-updater/service.py

chown root:root /usr/local/dynamic-routing-updater/service.py

systemctl daemon-reload

systemctl enable dynamic-routing-updater.service
systemctl start dynamic-routing-updater.service

systemctl status dynamic-routing-updater.service