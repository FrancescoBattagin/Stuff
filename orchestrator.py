#!/usr/bin/env python2
import grpc
import os, sys
from time import sleep
from scapy.all import *
from mysql.connector import connect, Error
from getpass import getpass


# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 'utils/p4runtime_lib'))
import bmv2
from error_utils import printGrpcError
from switch import ShutdownAllSwitchConnections
import helper

def checkPolicies(packet):
    #TODO db query, now managed as file.txt read
    policies = []
    with open("policiesDB.txt", 'r') as f:
        print("policiesDB.txt opened")
        line = f.readline()
        while line:
            policies.append(line.split(" "))
            line = f.readline()
    lookForPolicy(policies, packet)


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
    for policy in policies:
        #TODO managed different types of policies -> see when they'll be defined
        if packet[0][IP].src in policy and packet[0][IP].dst in policy: #&& desired info are present
        addEntries(packet[0][IP].src, packet[0][IP].dst)          
        break
    if not found:
        #packet drop
        packet = None
        print("packet dropped")

def addEntries(ip_src, ip_dst):
    te = p4info_helper.buildTableEntry(
        table_name="my_ingress.ipv4_lpm",
        match_fields={
            "hdr.ipv4_t.srcAddr": ip_src,
            "hdr.ipv4_t.dstAddr": ip_dst
        },
        action_name="my_ingress.ipv4_forward",
        action_params={}
    )
    ces.WriteTableEntry(te)
    print("Installed leader table entry rule on ces")



p4info_file_path = "p4-test.p4info.txt"
p4info_helper = helper.P4InfoHelper(p4info_file_path)
ces = bmv2.Bmv2SwitchConnection(
    name='ces',
    address='192.187.3.7:50051',
    device_id= 0,
    proto_dump_file='logs/ces-p4runtime.txt')

ces.MasterArbitrationUpdate()

while True:
    packet = None
    print("Waiting for receive something")
    
    time.sleep(0.2)
    packet = sniff(count = 1)
    
    # if packet != None:
    #     if str(packet[0][ICMP].type) == "8": 
    #         print("PING from " + packet[0][IP].src)
    #     else:
    print("Packet received!: " + packet[0][IP].src + "-->" + packet[0][IP].dst)
    print(packet)
    checkPolicies(packet)
