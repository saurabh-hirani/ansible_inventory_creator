#!/usr/bin/env python
"""
Create Ansible icinga2 inventory using ansible_inventory_creator

Pre-requisites:

- An icinga2 setup running with the API feature enabled
- Python module icinga2_api and update its config file
- icinga2.json in the same directory as this program

Example:

$ cat > icinga2.json
{
  "stage": {
    "configfile": "/home/xyz/.icinga2/api.yml"
  }
} # where 'stage' is the icinga2 api profile and the file path is corresponding config

$ ICINGA2_API_PROFILE=stage python icinga2_inventory --list

$ ICINGA2_API_PROFILE=stage python icinga2_inventory --host $host_ip
"""

from __future__ import print_function
import os
import sys
import json
import copy

from icinga2_api import api
import ansible_inventory_creator.main

def do_list(args):
  """ --list callback """
  configfile = args['configfile']
  profile = args['profile']

  obj = api.Api(configfile=configfile, profile=profile)
  uri = '/v1/objects/hosts'

  if args['verbose']:
    print('STATUS: querying icinga2_api: %s' % uri)

  output = obj.read(uri)

  if output['response']['status_code'] != 200:
    sys.stderr.write('ERROR: icinga2 API query failed\n')
    sys.stderr.write(json.dumps(output, indent=2))
    sys.exit(1)

  inventory_ds = {
    '_meta': {
      'hostvars': {
      }
    }
  }

  for host_data in output['response']['data']['results']:
    host_name = host_data['attrs']['display_name']
    host_addr = host_data['attrs']['address']
    log_prefix = 'STATUS: %s: %s' % (host_name, host_addr)

    if args['verbose']:
      print('%s: adding' % log_prefix)

    host_groups = host_data['attrs']['groups']
    for host_group in host_groups:
      if host_group not in inventory_ds:
        inventory_ds[host_group] = {'hosts': []}
      inventory_ds[host_group]['hosts'].append(host_addr)
    inventory_ds['_meta']['hostvars'][host_addr] = copy.deepcopy(host_data['attrs'])

  return inventory_ds

def do_host(args):
  """ --host callback """
  return args['list_ds']['_meta']['hostvars'][args['host']]

def create_inventory():
  """ Wrapper to call inventory creator """

  configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icinga2.json')
  config = json.loads(open(configfile).read())

  if 'ICINGA2_API_PROFILE' not in os.environ:
    sys.stderr.write('ERROR: Did not specify icinga2 API profile\n')
    sys.exit(1)

  profile = os.environ['ICINGA2_API_PROFILE']

  list_callback = {
    'function': do_list,
    'args': {
      'configfile': config[profile]['configfile'],
      'profile': profile
    }
  }

  host_callback = {
    'function': do_host,
    'args': {}
  }

  return ansible_inventory_creator.main.create(list_callback=list_callback,
                                               host_callback=host_callback)

def main():
  """ The main workhorse """
  print(json.dumps(create_inventory(), indent=2))

if __name__ == "__main__":
  main()
