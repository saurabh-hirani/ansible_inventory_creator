#!/usr/bin/env python

from __future__ import print_function

import multiprocessing as mp
import socket

def port_checker(host, port, status_queue, verbose=False):
  """ Worker checking if host has a specific port open and updating status queue """
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(5)

  if verbose:
    print('STATUS: %s: %s: checking connectivity' % (host, port))

  try:
    result = sock.connect_ex((host, port))
  except Exception as e:
    result = 1

  if result == 0:
    status_queue.put(('open', host))
  else:
    status_queue.put(('closed', host))

  sock.close()

def port_conn_status(hosts, port, verbose=False):
  """ Check if hosts have a specific port open - uses multiprocessing """
  status_queue = mp.Queue()
  processes = [mp.Process(target=port_checker, args=(host, port, status_queue, verbose)) \
               for host in set(hosts)]
  for proc in processes:
    proc.start()

  open_closed_hosts = [status_queue.get() for _ in processes]

  overall_status = {
    'open': [],
    'closed': []
  }

  for status, host in open_closed_hosts:
    if status == 'open':
      overall_status['open'].append(host)
    else:
      overall_status['closed'].append(host)

  return overall_status

def get_all_hosts(list_ds, verbose=False):
  """ Get all hosts from an ansible dynamic inventory program output """
  if 'all' in list_ds:
    if 'hosts' in list_ds['all'] and list_ds['all']['hosts']:
      return list_ds['all']['hosts']

  if verbose:
    print('STATUS: creating the [all] hostgroup')

  all_hosts = set()

  for _, hosts_ds in list_ds.items():
    if 'hosts' not in hosts_ds:
      continue
    all_hosts |= set(hosts_ds['hosts'])

  return list(all_hosts)
