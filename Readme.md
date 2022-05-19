# Getting started with InnoDB Cluster tutorial

Tutorial presented at Percona Live 2022 - Austin, TX
Presntation link: https://sched.co/10Iua

## Authors:
- Jakob Lorberblatt, lorberblatt@pythian.com
- Matthias Crauwels, crauwels@pythian.com

## How to

This playbook was designed to run on CentOS 8 Stream or Rocky Linux 8 and Ansible 2.12

1. Install the OS on a machine
2. Install package `ansible-core` on your machine
  ```
    yum install ansible-core
  ```
3. Install ansible dependencies
  ```
    ansible-galaxy collection install -r requirements.yml
  ```
4. Apply the playbook
  ```
    ansible-playbook -i inventory main.yml
  ```

## What this will do

This playbook will deploy a 3 instance MySQL 8.0.28 setup
- `mysql1` listening on 127.0.0.1 port 3301, acting as writer server (master)
- `mysql2` listening on 127.0.0.1 port 3302, acting as async replica
- `mysql3` listening on 127.0.0.1 port 3303, acting as async replica

These instances are designed to be demo-instances and are not setup up to best practices. You can connect using user `root` without a password.

Apart from the MySQL deployment, and `haproxy` service is running with 3 listeners:
- listener on port 3306, proxying for the writer server (RW connections)
- listener on port 3307, proxying for the reads (balancing between all 3 servers)
- listener on port 8000, for haproxy stats (`http://<server-address>:8000/haproxy/stats` , username: `user`, password `pass`)

Finally a small Python app is running generating read and write traffic on the deployment.
- Application stats can be found on `http://<server-address>:5000`
- Application config file is at `/etc/application/config.yaml`
- Application service is configured by `systemd` (ex: `systemctl status application.service`)


**This lab is intended for testing purposes only.**
