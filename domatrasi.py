#!/usr/bin/python3
''' This is a script for getting information from an opensrs domain by API

'''
import argparse
import requests
import hashlib
import sys
import apikey
import json 

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d", metavar='<domain name>', help="domain name to check <e.g. btitalia.it> ", type=str )
group.add_argument("-f", metavar='<file name>', help="text file containing domains name to check one for line <e.g. domain_lists.txt> ")
parser.add_argument("mode", help="0 or 1 - 0 for real operation and 1 just for test  ", type=int )
parser.add_argument("-v", "--verbosity", help="output operation on screen", action = "store_true")
args = parser.parse_args()
#print(args)
#print(apikey.api_key)

dominio = args.d
''' get domain name from first parameter in the command string '''
TEST_MODE = args.mode
#''' get Test Mode from the second parameter in the command string '''

xml = '''
<?xml version='1.0' encoding='UTF-8' standalone='no' ?>
<!DOCTYPE OPS_envelope SYSTEM 'ops.dtd'>
<OPS_envelope>
<header>
    <version>0.9</version>
</header>
<body>
<data_block>
    <dt_assoc>
        <item key="protocol">XCP</item>
        <item key="action">GET</item>
        <item key="object">DOMAIN</item>
        <item key="attributes">
            <dt_assoc>
                <item key="domain">'''+dominio+'''</item>
                <item key="type">domain_auth_info</item>
            </dt_assoc>
        </item>
    </dt_assoc>
</data_block>
</body>
</OPS_envelope>
'''
print(xml)
