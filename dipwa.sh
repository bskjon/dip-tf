#!/bin/sh

#if [ -f "/tmp/dipwa" ]; then
#    chmod 0600 /tmp/dipwa
#else
#    exit 1
#fi
echo "DIPWA: Registered change to network adpater $IFACE"

if [ ! -z $IFACE ]
then
    echo $IFACE > /tmp/dipwa
fi
