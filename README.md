### Ansible Inventory Creator

Because one life is too short to write the same boilerplate code for each Ansible dynamic inventory script.

### Why

Ansible supports [dynamic inventories](http://docs.ansible.com/ansible/intro_dynamic_inventory.html) where hosts and their attributes are queried from an external source e.g. AWS, Chef, etc.

There are many user contributed inventories as seen [here](https://github.com/ansible/ansible/tree/devel/contrib/inventory). But all of them rewrite the logic for the following features in each script:

  - Command line parsing
  - Caching e.g [ec2.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.py) and [gce.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/gce.py)

This could very well be abstracted out in a library which should just need **--list** and **--host** callbacks from the user and do implement the above functionality.

  - Also each script, although contained has its own convention of layout e.g. [ec2.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.py) and a few others have the follow call structure:

  - Call XInventory e.g. Ec2Inventory, GceInventory, etc. directly without the:

  ```
  if __name__ == '__main__':
  ```

  e.g. [ec2.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.py), [gce.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/gce.py)

  block, while some use the if-main structure e.g. [cloudstack.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/cloudstack.py), [vmware.py](https://github.com/ansible/ansible/blob/devel/contrib/inventory/vmware.py)

  - When you want to write a custom inventory script, the less code you copy paste from an existing inventory script - the better.

That is why this repo exists.

### Installation

* To install a stable release:

  ```pip install ansible_inventory_creator```

* To install the development package:

  ```
  git clone https://github.com/saurabh-hirani/ansible_inventory_creator
  sudo ./install.sh
  ```
* Remove files installed by ```./install.sh```

  ```
  sudo ./uninstall.sh
  ```

### Usage

* Check [examples](https://github.com/saurabh-hirani/ansible_inventory_creator/examples)
