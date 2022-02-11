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

systemctl daemon-reload

sleep 10s

mkdir --parents /usr/local/dip-table-flipper/
cp ./service.py /usr/local/dip-table-flipper/service.py
cp ./reference.json /usr/local/dip-table-flipper/reference.json
cp ./dipwa.sh /etc/networkd-dispatcher/routable.d/dipwa.sh
cp ./dipwa.sh /usr/lib/networkd-dispatcher/routable.d/dipwa.sh

referenceAbsPath="/usr/local/dip-table-flipper/reference.json"
sed -i "s^reference.json^$referenceAbsPath^g" /usr/local/dip-table-flipper/service.py


cat > /etc/systemd/system/dip-table-flipper.service <<EOL
[Unit]
Description=Dynamic IP Service - Table Flipper

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python3 -u /usr/local/dip-table-flipper/service.py
Environment=PYTHONUNBUFFERED=1


[Install]
WantedBy=multi-user.target
EOL

chmod 700 /etc/networkd-dispatcher/routable.d/dipwa.sh
chmod 700 /usr/lib/networkd-dispatcher/routable.d/dipwa.sh

chmod 700 /usr/local/dip-table-flipper/service.py

chown root:root /usr/local/dip-table-flipper/service.py

systemctl daemon-reload

systemctl enable dip-table-flipper.service
systemctl start dip-table-flipper.service

systemctl status dip-table-flipper.service