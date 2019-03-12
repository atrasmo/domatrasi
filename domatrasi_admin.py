#!/usr/bin/python3
import argparse
import requests
import hashlib
import apikey
import re
from xml.sax.saxutils import unescape

def doitbydomain(connection_details,dominio):
    ''' function that give you the auth_info passing domain_name '''

    xml = '''
    <?xml version='1.0' encoding="UTF-8" standalone="no"?>
    <!DOCTYPE OPS_envelope SYSTEM "ops.dtd">
    <OPS_envelope>
        <header>
            <version>0.9</version>
        </header>
        <body>
            <data_block>
                <dt_assoc>
                    <item key="protocol">XCP</item>
                    <item key="object">DOMAIN</item>
                    <item key="action">GET</item>
                    <item key="domain">'''+dominio+'''</item>
                    <item key="attributes">
                        <dt_assoc>
                            <item key="type">owner</item>
                        </dt_assoc>
                    </item>
                </dt_assoc>
            </data_block>
        </body>
    </OPS_envelope>
    '''

    md5_obj = hashlib.md5()
    md5_obj.update((xml + connection_details['api_key']).encode('utf-8'))
    signature = md5_obj.hexdigest()

    md5_obj = hashlib.md5()
    md5_obj.update((signature + connection_details['api_key']).encode('utf-8'))
    signature = md5_obj.hexdigest()

    headers = {
            'Content-Type':'text/xml',
            'X-Username': connection_details['reseller_username'],
            'X-Signature':signature,
    }

    #debug points
    #print ('***********************************',xml,'***********************************')
    r = requests.post(connection_details['api_host_port'], data = xml, headers=headers )

    if r.status_code == requests.codes.ok:
        print(r.text)
        #print (r.status_code)
        oup = re.search(r"org_name\">(.*)<",r.text).group(1)
        oup = oup +"|"+ re.search(r"email\">(.*)<",r.text).group(1)
        return oup
    else:
        return (r.status_code)
        #_filewr.write(r.status_code)
        #print (r.text)
        #_filewr.write(r.text)


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-d", metavar='<domain name>', help="domain name to check <e.g. btitalia.it> ", type=str )
group.add_argument("-f", metavar='<file name>', help="text file containing domains name to check one for line <e.g. domain_lists.txt> ")
parser.add_argument("-mode", help="0 or 1 - 0 for real operation and 1 just for test  ", type=int, default=0 )
parser.add_argument("-v", "--verbosity", help="output operation on screen", action = "store_true")
args = parser.parse_args()
#debug points
#print(args)
#print(apikey.api_key)

dominio = args.d
''' get domain name from first parameter in the command string '''
TEST_MODE = args.mode
''' get Test Mode from the second parameter in the command string '''

connection_options = {
        'live' : {
         # IP whitelisting required
             'reseller_username': apikey.username,
             'api_key': apikey.api_key,
             'api_host_port': 'https://rr-n1-tor.opensrs.net:55443',
        },
        'test' : {
             # IP whitelisting not required
             'reseller_username': apikey.username,
             'api_key': apikey.api_key,
             'api_host_port': 'https://horizon.opensrs.net:55443',
            }
}


if TEST_MODE == 1:
    connection_details = connection_options['test']
else:
    connection_details = connection_options['live']

entities={
    "&apos;":"'"
}

if (args.f != None):
    _filewr = open(args.f+"_log", "w")
    try:
        with open(args.f) as filein :
            for dominio in filein:
                dominio= dominio.rstrip("\n")
                auth_code = doitbydomain(connection_details, dominio)
                print(dominio + "|" + unescape(auth_code,entities))
                _filewr.write(dominio + "|" +unescape(auth_code,entities)+"\n")
            filein.close()
            _filewr.close()
    except IOError as e:
        print ("Unable to open file , Does not exist or no read permissions")
else:
    auth_code = doitbydomain(connection_details, dominio)
    print(dominio + "|" + unescape(auth_code, entities) + "\n")
