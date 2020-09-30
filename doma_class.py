#!/usr/bin/python3
'''
Atrasmo forked form opensrs.py
https://domains.opensrs.guide/docs/
'''

from xml.etree.ElementTree import fromstring, tostring, SubElement, Element
import requests
import hashlib
import apikey
import argparse

class OpenSRS(object):
  VERSION = '0.9'
  server = None
  username = None
  private_key = None

  def __init__(self, username, private_key, test=False):
    '''
    Constructor: sets the username, private key and test mode

    Parameters:
    username - your OpenSRS username
    private_key - your OpenSRS private key
    test - set to False for production operation
    '''
    self.username = username
    self.private_key = private_key
    if test: self.server = 'https://horizon.opensrs.net:55443'
    else: self.server = 'https://rr-n1-tor.opensrs.net:55443'

  def xml(self, action, object, attrs, extra_items=None):
    '''
    Post: send an action to the OpenSRS API

    Parameters:
    action - the name of the action (ie. sw_register, name_suggest, etc)
    object - the object type to operate on (ie. domain, trust_service)
    attrs - a data struct to construct the attributes from (see example)
    extra_items - any extra top level items (ie. registrant_ip)
    '''
    def data_to_xml(elm, key, data):
      '''
      data_to_xml adds a item sub element to elm and then sets the
      text if its not a list or dict, otherwise it recurses
      '''
      item = SubElement(elm, 'item', {'key':key})
      if isinstance(data, dict):
        data_to_dt_assoc(item, data)
      elif isinstance(data, list):
        data_to_dt_array(item, data)
      else:
        item.text = str(data)
      return item

    def data_to_dt_assoc(elm, data):
      '''
      Adds an associative array of data in the format that opensrs
      requires, uses data_to_xml to recurse
      '''
      _dt_assoc = SubElement(elm, 'dt_assoc')
      for key in data.keys():
        data_to_xml(_dt_assoc, key, data[key])

    def data_to_dt_array(elm, list):
      '''
      Adds an list of data in the format that opensrs requires,
      uses data_to_xml to recurse
      '''
      _dt_array = SubElement(elm, 'dt_array')
      key = 0
      for ent in list:
        data_to_xml(_dt_array, str(key), ent)
        key += 1

    root = Element("OPS_envelope")
    header = SubElement(root, 'header')
    version = SubElement(header, 'version')
    version.text = str(self.VERSION)
    body = SubElement(root, 'body')
    data_block = SubElement(body, 'data_block')
    params = {
      'protocol': 'XCP',
      'action': action,
      'object': object,
      'attributes': attrs,
    }
    if isinstance(extra_items, dict): params.update(extra_items)
    data_to_dt_assoc(data_block, params)
    return "<?xml version='1.0' encoding='UTF-8' standalone='no' ?>%s" % tostring(root)

  def post(self, action, object, attrs, extra_items=None):
    def xml_to_data(elm, is_list=False):
      '''
      This converts an element that has a bunch of 'item' tags
      as children into a Python data structure.

      If is_list is true it is assumed that the child items all
      have numeric indices and should be treated as a list, else
      they are treated as a dict
      '''
      if is_list:
        data = []
      else:
        data = {}
      for child in elm:
        if child.tag != 'item': continue
        if len(child) > 0:
          if child[0].tag == 'dt_assoc':
            new_data = xml_to_data(child[0])
          elif child[0].tag == 'dt_array':
            new_data = xml_to_data(child[0], is_list=True)
        else:
          new_data = str(child.text)
        key = child.get('key')
        if is_list:
          data.insert(int(key), new_data)
        else:
          data[key] = new_data
      return data

    body = self.xml(action, object, attrs, extra_items)
    #signature = hashlib.md5("%s%s" % (hashlib.md5("%s%s" % (body, self.private_key)).hexdigest(), self.private_key)).hexdigest()

    md5_obj = hashlib.md5()
    md5_obj.update((body + self.private_key).encode('utf-8'))
    signature = md5_obj.hexdigest()

    md5_obj = hashlib.md5()
    md5_obj.update((signature + self.private_key).encode('utf-8'))
    signature = md5_obj.hexdigest()


    headers = {
      'Content-Type':'text/xml',
      'X-Username': self.username,
      'X-Signature': signature,
      'Content-Length': str(len(body)),
    }
    try:
      r = requests.post(self.server, data=body, headers=headers)
    except Exception as e:
      return '-ERR: %s' % e

    if r.status_code != 200:
      return '-ERR %d: %s' % (r.status_code, r.text)

    xml = fromstring(r.content)
    version = xml.find('header/version')
    if version is None:
      return '-ERR: response-no-version.\n%s' % r.text
    if version.text > self.VERSION:
      return '-ERR: response version %s is newer than us %s.\n%s' % (version.text, self.VERSION, r.text)
    dt_assoc = xml.find('body/data_block/dt_assoc')
    if dt_assoc is None:
      return '-ERR: response does not have body/data_block/dt_assoc.\n%s' % r.text
    return xml_to_data(dt_assoc)

  def get_domains_by_expiredate(self, exp_to=None, exp_from='1989-12-31', limit=200, page=1):
    '''
    Retrieves domains that expire within a specified date range.

    exp_from | Required | Used in conjunction with exp_to attribute.
                          The date from which to list expiring domains.
                          Date must be in the format YYYY-MM-DD.

    exp_to   | Required | Used in conjunction with exp_from attribute.
                          The date until which to list expiring domains.
                          Date must be in the format YYYY-MM-DD.

    limit    | Optional | The number of domains to return on each page.
               ( 40 )

    page     | Optional | Determines which page to retrieve, using
               ( 1 )      the page number. The page index starts at
                          0 (zero).
    '''
    import datetime
    now = datetime.datetime.now()
    if exp_to is None: exp_to = now.strftime('%Y-%m-%d')
    return self.post('get_domains_by_expiredate', 'domain', {
      'exp_from': exp_from,
      'exp_to': exp_to,
      'limit': limit,
      'page': page,
    })

  def get_transfers_away(self):
    '''
    '''
    return self.post('get_transfers_away', 'domain', {})

  def get(self, domain_name, typ='all_info', max_to_expiry=0, min_to_expiry=0, limit=200, page=1):
    '''
    typ = all_info |  billing | ca_whois_display_setting |
          domain_auth_info | expire_action | forwarding_email | list |
          nameservers | owner | rsp_whois_info | status | tech |
          tld_data | waiting_history | whois_privacy_state

    note: typ=list with max/min_to_expiry does NOT work returns 415 error ?!
    '''
    return self.post('get', 'domain', {
      'type':typ,
      'domain':domain_name,
      'limit': limit,
      'page': page,
    })

  def update_nameservers(self, domain_name, nameservers):
    '''
    '''
    return self.post('advanced_update_nameservers', 'domain', {
      'domain':domain_name,
      'op_type': 'assign',
      'assign_ns':nameservers
    })

  def nameserver_list(self, domain_name):
    return [ns['name'] for ns in self.get(domain_name, 'nameservers')['attributes']['nameserver_list']]

def get_domains(opensrs):
  '''
  no-error-checking of responses
  '''
  dlist = []
  for d in opensrs.get_domains_by_expiredate('2020-12-31')['attributes']['exp_domains']:
    dlist.append(d['name'] + ' ' + ' '.join(opensrs.nameserver_list(d['name'])))
  return '\n'.join(dlist)

def main():
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-d", metavar='<domain name>', help="domain name to check <e.g. btitalia.it> ", type=str )
  group.add_argument("-f", metavar='<file name>', help="text file containing domains name to check one for line <e.g. domain_lists.txt> ")
  parser.add_argument("-mode", help="0 or 1 - 0 for real operation and 1 just for test  ", type=int, default=0 )
  parser.add_argument("-v", "--verbosity", help="output operation on screen", action = "store_true")
  args = parser.parse_args()

  dominio = args.d

  opensrs = OpenSRS(apikey.username, apikey.api_key  , test=False)
  
  if (args.f != None):
      print("ok")
  else:
      roba= opensrs.get(dominio,"all_info")
      pprint.pprint(roba)
  

if __name__ == '__main__':
  main()
