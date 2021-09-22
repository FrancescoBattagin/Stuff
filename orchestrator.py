#!/usr/bin/env python2
#import argparse
import grpc
import os
import sys
import p4runtime_sh.shell as sh
from p4runtime_sh.shell import PacketIn
from time import sleep
from scapy.all import *
import yaml
# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
# import p4runtime_lib.bmv2
# from p4runtime_lib.switch import ShutdownAllSwitchConnections
# import p4runtime_lib.helper

def checkPolicies(pkt):
    #TODO yaml parsing, now managed as file.txt read
    #policies = []
    #with open("policiesDB.txt", 'r') as f:
    #    print("policiesDB.txt opened")
    #    line = f.readline()
    #    while line:
    #        policies.append(line.split(" "))
    #        line = f.readline()

    stream = open("policiesDB.yaml", 'r')
    policies_list = yaml.safe_load(stream)
    #for key, value in policies.items():
    #    print (key + " : " + str(value))

    lookForPolicy(policies_list, pkt)

def checkPoliciesDB(packet):
    policies = []
    try:
        with connect(
            host="localhost",
            user=input("Enter your username: "),
            password=input("Enter your password: "),
            database="Policydb"
        ) as connection:
            print(connection)
            prepared_statement = "SELECT * FROM policies"
            with connection.cursor() as cursor:
                cursor.execute(prepared_statement)
                policies = cursor.fetchall()
            print(policies)
            lookForPolicy(policies, packet)

    except Error as e:
        print(e)


def lookForPolicy(policyList, packet):
    found = False
    print("Policies: \n")
    print(policyList)
    
    src = pkt.getlayer(IP).src
    dst = pkt.getlayer(IP).dst
    srcAddr = pkt.getlayer(Ether).src
    switchAddr = pkt.getlayer(Ether).dst
    #pkt_tcp = pkt.getlayer(TCP)
    #pkt_udp = pkt.getlayer(UDP)
    #if pkt_tcp != None:
    #    print("protocol: TCP")
    #    sport = pkt_tcp.sport
    #    dport = pkt_tcp.dport
    #elif pkt_udp != None:
    #    print("protocol = UDP")
    #    sport = pkt_udp.sport
    #    dport = pkt_udp.dport
    #else:
    #   print("protocol unknown")

    print("src: " + src)
    print("dst: " + dst)
    print("scr: " + srcAddr)
    print("switchAddr: " + switchAddr)

    #print("dport: " + str(dport))
    #print("sport: " + str(sport))
    pkt_icmp = pkt.getlayer(ICMP)
    pkt_ip = pkt.getlayer(IP)

    for policy in policyList:
        #policy_tuple.get("dst")
        if src == policy.get("src") and dst == policy.get("dst"):# and str(dport) == policy.get("dport")): #sport not needed?
            dst_ethernet = policy.get("dst_ethernet")
            print("dst_ethernet: " + dst_ethernet)
            addEntries(src, dst, dst_ethernet)#also dport and protocol
            #add bi-directional entry if icmp packet!
            if pkt_icmp != None and pkt_ip != None and str(pkt_icmp.getlayer(ICMP).type) == "8":
                addEntries(dst, src, srcAddr)#also sport and protocol
            found = True
            break
    if not found:
        #packet drop
        packet = None
        print("packet dropped")

def addEntries(ip_src, ip_dst, dstAddr):#add port and protocol
    te = sh.TableEntry('my_ingress.ipv4_exact')(action='my_ingress.ipv4_forward')
    te.match["hdr.ipv4.srcAddr"] = ip_src
    te.match["hdr.ipv4.dstAddr"] = ip_dst
    te.action["dstAddr"] = dstAddr
    if dstAddr == H2_ETH:
        te.action["port"] = SWITCH_TO_HOST2_PORT
    else:
        te.action["port"] = HOST1_TO_SWITCH_PORT
    te.insert()
    print("[!] New entry added")


def packetHandler(streamMessageResponse):
    print("Packets received")
    packet = streamMessageResponse.packet

    if streamMessageResponse.WhichOneof('update') =='packet':
        packet_payload = packet.payload
        pkt = Ether(_pkt=packet.payload)
        
        if pkt.getlayer(IP) != None:
            pkt_src = pkt.getlayer(IP).src
            pkt_dst = pkt.getlayer(IP).dst
        ether_type = pkt.getlayer(Ether).type
        pkt_icmp = pkt.getlayer(ICMP)
        pkt_ip = pkt.getlayer(IP)

        print("ether_type: " + str(ether_type))
        
        if pkt_icmp != None and pkt_ip != None and str(pkt_icmp.getlayer(ICMP).type) == "8":
            print("PING from: " + pkt_src)
            checkPolicies(pkt)
        elif pkt_ip != None:
            print("Packet received!: " + pkt_src + "-->" + pkt_dst)
            checkPolicies(pkt)
        else:
            print("No needed layer (ARP, DNS, ...)")

def controller():

    sh.setup(
        device_id=0,
        grpc_addr='localhost:50051',
        election_id=(1, 0), # (high, low)
        config=sh.FwdPipeConfig('p4-test.p4info.txt','p4-test.json')
    )

    while True:
        packets = None
        print("Waiting for receive something")
        packet_in = sh.PacketIn()
        packets = packet_in.sniff(timeout=5)
        for streamMessageResponse in packets:
            packetHandler(streamMessageResponse)

if __name__ == '__main__':
    controller()