#!/usr/bin/env python

""" Ansible inventory creation helpers """

from __future__ import print_function

import os
import time
import argparse
import json
import re
import utils

# TODO
# have config files - /etc/, ~/., local dir

# defaults for helpers
ANSIBLE_DYN_INV_DEFAULTS = {
  'ANSIBLE_DYN_INV_CACHE': 'false',
  'ANSIBLE_DYN_INV_CACHE_PATH': os.path.join(os.path.expanduser('~'),
                                             '.ansible-inventory-cache.json'),
  'ANSIBLE_DYN_INV_CACHE_MAX_AGE': '3600',
  'ANSIBLE_DYN_INV_ALL_HOSTGROUP': 'false',
  'ANSIBLE_DYN_INV_SSH_HOSTGROUPS': 'false'
}

# duh
SSH_PORT = 22

class InvalidArgument(ValueError):
  """ Custom exception for invalid arg """
  pass

class InventoryCache(object):
  """ Inventory cache class """
  def __init__(self, path, max_age):
    """ Create the object """

    self.path = path
    self.max_age = max_age

    if re.match(r'^\d+$', str(self.max_age)) is None:
      raise InvalidArgument('ERROR: Invalid cache max_age: %s\n' % self.max_age)

    self.max_age = int(self.max_age)

  def exists(self):
    """ Check if cache exists """
    return os.path.isfile(self.path)

  def is_valid(self):
    """ Check if cache is valid """
    if self.exists():
      mod_time = os.path.getmtime(self.path)
      current_time = time.time()
      if (mod_time + self.max_age) > current_time:
        return True
    return False

  def dump(self, data):
    """ Dump data to cache """
    with open(self.path, 'w') as file_desc:
      file_desc.write(json.dumps(data, indent=2))
    return data

  def load(self):
    """ Load data from cache """
    return json.loads(open(self.path).read())

class Inventory(object):
  """ Ansible Inventory base class """
  def __init__(self, **kwargs):
    """ Create the object """
    # load defaults
    for env_var in ANSIBLE_DYN_INV_DEFAULTS:
      if env_var not in os.environ:
        os.environ[env_var] = ANSIBLE_DYN_INV_DEFAULTS[env_var]

      val = os.environ[env_var]
      if val == 'true':
        val = True
      elif val == 'false':
        val = False

      # create instance attributes from env vars
      setattr(self, env_var.lower(), val)

    self.list_callback = kwargs.pop('list_callback')
    self.host_callback = kwargs.pop('host_callback')

    # Parse cmdline
    self.cmdline_args = {}
    self.parse_cmdline()

    self.list_callback['args'].update(self.cmdline_args)
    self.host_callback['args'].update(self.cmdline_args)

    # create cache object indepentdent of the inventory
    self.cache = None
    if self.ansible_dyn_inv_cache:
      self.cache = InventoryCache(self.ansible_dyn_inv_cache_path,
                                  self.ansible_dyn_inv_cache_max_age)

    # list_ds - create for --list action
    self.list_ds = None

    # host_ds - create for --host action
    self.host_ds = None

    # default - don't load from cache
    self.load_from_cache = False

  def parse_cmdline(self):
    """ Parse cmdline args """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='json string having config for this inventory',
                        default='')
    parser.add_argument('-l', '--list', help='List inventory', action='store_true',
                        default=False)
    parser.add_argument('-r', '--refresh-cache', help='Refresh cached inventory',
                        action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='Verbose mode',
                        action='store_true', default=False)
    parser.add_argument('--host', help='host to query', default=False,
                        required=False)
    self.cmdline_args = vars(parser.parse_args())
    return self.cmdline_args

  def create_hostgroup_all(self):
    """ create "all" hostgroup if enabled """
    all_hosts = []
    if not self.load_from_cache:
      all_hosts = utils.get_all_hosts(self.list_ds, self.cmdline_args['verbose'])
      self.list_ds['all'] = all_hosts

  def create_hostgroup_ssh(self):
    """ Create "can_ssh", "cannot_ssh" hostgroup if enabled """
    if 'all' not in self.list_ds:
      self.create_hostgroup_all()

    if not self.load_from_cache:
      ssh_status = utils.port_conn_status(self.list_ds['all'], SSH_PORT,
                                          self.cmdline_args['verbose'])
      self.list_ds['can_ssh'] = {'hosts': []}
      self.list_ds['cannot_ssh'] = {'hosts': []}
      self.list_ds['can_ssh']['hosts'] = list(ssh_status['open'])
      self.list_ds['cannot_ssh']['hosts'] = list(ssh_status['closed'])

  def del_hostgroup(self, hostgroup):
    """ delete a hostgroup from self.list_ds """
    if hostgroup in self.list_ds:
      del self.list_ds[hostgroup]

  def execute(self):
    """ Execute action based on the cmdline args """

    if self.cache and self.cache.is_valid() and not self.cmdline_args['refresh_cache']:
      self.load_from_cache = True
      if self.cmdline_args['verbose']:
        print('STATUS: loading from cache: %s' % self.ansible_dyn_inv_cache_path)
      self.list_ds = self.cache.load()
    else:
      self.list_ds = self.list_callback['function'](self.list_callback['args'])

    if self.ansible_dyn_inv_all_hostgroup:
      self.create_hostgroup_all()
    else:
      self.del_hostgroup('all')

    if self.ansible_dyn_inv_ssh_hostgroups:
      self.create_hostgroup_ssh()
    else:
      self.del_hostgroup('can_ssh')
      self.del_hostgroup('cannot_ssh')

    # If caching is enabled and we didn't load from cache - we'd better save it
    # to the cache
    if self.cache and not self.load_from_cache:
      print('STATUS: dumping to cache: %s' % self.ansible_dyn_inv_cache_path)
      self.cache.dump(self.list_ds)

    if self.cmdline_args['list']:
      return self.list_ds

    if self.cmdline_args['host']:
      self.host_callback['args']['list_ds'] = self.list_ds
      self.host_callback['args']['host'] = self.cmdline_args['host']
      return self.host_callback['function'](self.host_callback['args'])

def create(**kwargs):
  """ Wrapper over BaseInventory class """
  inventory_obj = Inventory(**kwargs)
  return inventory_obj.execute()
