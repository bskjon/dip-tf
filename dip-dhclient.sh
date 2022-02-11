#! /bin/sh

tableOne="ingressOne"
tableTwo="ingressTwo"

interfaceOne="enp1s0f0"
interfaceTwo="enp1s0f1"


getGateway()
{
        gw=$(netplan ip leases $1 | grep -oP '(?<=(^ROUTER=)).*')
	echo $gw
}

getSubnet()
{
        net=$(netplan ip leases $1 | grep -oP '(?<=(^NETMASK=)).*')
        subnetIp=$(getGateway $1 | grep -oP '\d+(\.\d+){2}')
        mask=$(getMaskFromSubnet $net)
        subnet=${subnetIp}".0"${mask}
	echo $subnet
}

getMaskFromSubnet()
{
        #$1 = Subnet (255.255.240.0)

        if [ $1 = "255.0.0.0" ]; then
                echo "/8"
        elif [ $1 = "255.128.0.0" ]; then
                echo "/9"
        elif [ $1 = "255.192.0.0" ]; then
                echo "/10"
        elif [ $1 = "255.224.0.0" ]; then
                echo "/11"
        elif [ $1 = "255.240.0.0" ]; then
                echo "/12"
        elif [ $1 = "255.248.0.0" ]; then
                echo "/13"
        elif [ $1 = "255.252.0.0" ]; then
                echo "/14"
        elif [ $1 = "255.254.0.0" ]; then
                echo "/15"
        elif [ $1 = "255.255.0.0" ]; then
                echo "/16"
        elif [ $1 = "255.255.128.0" ]; then
                echo "/17"
        elif [ $1 = "255.255.192.0" ]; then
                echo "/18"
        elif [ $1 = "255.255.224.0" ]; then
                echo "/19"
        elif [ $1 = "255.255.240.0" ]; then
                echo "/20"
        elif [ $1 = "255.255.248.0" ]; then
                echo "/21"
        elif [ $1 = "255.255.252.0" ]; then
                echo "/22"
        elif [ $1 = "255.255.254.0" ]; then
                echo "/23"
        elif [ $1 = "255.255.255.0" ]; then
                echo "/24"
        elif [ $1 = "255.255.255.128" ]; then
                echo "/25"
        elif [ $1 = "255.255.255.192" ]; then
                echo "/26"
        elif [ $1 = "255.255.255.224" ]; then
                echo "/27"
        elif [ $1 = "255.255.255.240" ]; then
                echo "/28"
        elif [ $1 = "255.255.255.248" ]; then
                echo "/29"
        elif [ $1 = "255.255.255.252" ]; then
                echo "/30"
        fi
}


getIp()
{
        # $1 Interface

        ip=$(netplan ip leases $1 | grep -oP '(?<=(^ADDRESS=)).*')
	echo $ip
}

deleteRouting()
{    
    ip=$(getIp "$1")
    subnet=$(getSubnet "$1")
    gateway=$(getGateway "$1")

    printf "\nDeleting routes on main table\n\n"

#    printf "ip route del $subnet dev $1 src $ip table main\n"
#    printf "ip route del default via $gateway dev $1 src $ip table main\n"
#    printf "ip route del $gateway dev $i table main\n"

set -v
    ip route del $subnet dev $1 src $ip table main
    ip route del default via $gateway dev $1 src $ip table main
    #ip route del $gateway dev $i src $ip table main
    ip route del $gateway dev $1 table main
set +v


    printf "\nFlushing rules\n"
#    printf "ip route flush table $2\n"
set -v
    ip route flush table $2
set +v
    
    printf "\n"
}

setRouting()
{
    # $1 = Interface
    # $2 = Table

    now=`date`
    printf "\n\n============================  $now ================================\n"
    printf "\n\nSetting up routing for interface $1\n"

    ip=$(getIp "$1")
    subnet=$(getSubnet "$1")
    gateway=$(getGateway "$1")

    if [ -z $ip ]
    then
        return;
    fi


    printf "\tInterface: $1\n"
    printf "\tIp: $ip\n"
    printf "\tSubnet: $subnet\n"
    printf "\tGateway: $gateway\n"
    printf "\tOn table: $2\n"

    deleteRouting $1 $2

    # Adding Route to separate table
    printf "\nAdding Records to table $2\n"
    
#    printf "\nSetting route\n"
#    printf "\nip route add $subnet dev $1 src $ip table $2"
#    printf "\nip route add default via $gateway dev $1 src $ip table $2"
#    printf "\nip route add $gateway dev $1 src $ip table $2"

set -x
    ip route add $subnet dev $1 src $ip table $2
    ip route add default via $gateway dev $1 src $ip table $2
    ip route add $gateway dev $1 src $ip table $2
set +x



    printf "\n\nSetting rules\n"
#    printf "\nip rule add from $ip table $2"
#    printf "\nip rule add to $ip table $2"
set -v
    ip rule add from $ip table $2
set +v
    #ip rule add to $ip table $2



    printf "\n\n\n========================================   END  ========================================\n\n"


}

#printf "\nLoading Modprobe 802.1Q"
#modprobe 8021q

if [ $1 = "manual" ]; then
	printf "\n\n\nRunning dpi manually"
	setRouting "$interfaceOne" "$tableOne"
	setRouting "$interfaceTwo" "$tableTwo"
fi


if [ ! -z $IFACE ]
then
        if [ $interfaceOne = $IFACE ]
        then
                setRouting "$interfaceOne" "$tableOne" 2>&1 | tee -a /home/bskjon/dip.log
        elif [ $interfaceTwo = $IFACE ]
        then
                setRouting "$interfaceTwo" "$tableTwo" 2>&1 | tee -a /home/bskjon/dip.log
        fi

fi


#  2051  ip route del 84.213.224.0/20 dev enp1s0f0 proto kernel scope link src 84.213.233.93 table main
# 2052  sudo ip route del 84.213.224.0/20 dev enp1s0f0 proto kernel scope link src 84.213.233.93 table main
# 2054  ip route del 84.213.208.0/20 dev enp1s0f1 proto kernel scope link src 84.213.217.14 table main
# 2055  sudo ip route del 84.213.208.0/20 dev enp1s0f1 proto kernel scope link src 84.213.217.14 table main
# 2059  sudo ip route del 84.213.208.1 dev enp1s0f1 src 84.213.217.14
# 2061  ip route del 84.213.224.1 dev enp1s0f0
# 2062  sudo ip route del 84.213.224.1 dev enp1s0f0
# 2064  ip route del default via 84.213.224.1 dev enp1s0f0
# 2065  sudo ip route del default via 84.213.224.1 dev enp1s0f0
# 2075  ip route del 84.214.208.1
# 2076  sudo ip route del 84.214.208.1
# 2077  ip route del default via 84.213.224.1 dev enp1s0f0
# 2078  sudo ip route del default via 84.213.224.1 dev enp1s0f0
# 2081  sudo ip route del 84.213.224.1 dev enp1s0f0 scope link src 84.213.233.93
# 2109  history | grep del

