#!/usr/bin/env python3

import os
import json
import re
import time

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from subprocess import Popen, PIPE
from datetime import datetime

CONF_DIR='/etc/nginx/conf.d'
LE_DIR='/etc/letsencrypt'

def exec_cmd(cmd):
    stream = os.popen(cmd)
    output = stream.read()
    return output

def read_file(p):
    try:
        f = open(p)
        r = f.read()
        f.close()
        return r
    except:
        return None

def write_file(p, data):
    try:
        f = open(p, 'w')
        f.write(data)
        f.close()
        return True
    except:
        return None

def has_le(vhost):
    if (LE_DIR):
        le_vhost_dir = os.path.join(LE_DIR, 'live', vhost)
        fc_path = os.path.join(le_vhost_dir, 'fullchain.pem')
        return os.path.isfile(fc_path)
    return None

def get_le(vhost):
    ssl_cert = None
    ssl_cert_key = None

    if (has_le(vhost)):
        d = os.path.join('/etc', 'letsencrypt', 'live', vhost)
        ssl_cert = os.path.join(d, 'fullchain.pem')
        ssl_cert_key = os.path.join(d, 'privkey.pem')

    return ssl_cert, ssl_cert_key

def get_ssl_certs(vhost):
    ssl_cert, ssl_cert_key = get_le(vhost)

    if (not ssl_cert):
        ssl_cert = os.path.join('/etc', 'ssl', 'private', 'cert.pem')
        ssl_cert_key = os.path.join('/etc', 'ssl', 'private', 'key.pem')

    return ssl_cert, ssl_cert_key

def create_proxyconf(vhosts, hostname, port, ip):
    vhost = vhosts[0]
    tmpl = read_file('./proxied.conf.tmpl')
    proxy_addr = f'{ip}:{port}'

    ssl_cert, ssl_cert_key = get_ssl_certs(vhost)

    tmpl = tmpl.replace('%ip%', ip)
    tmpl = tmpl.replace('%hostname%', hostname)
    tmpl = tmpl.replace('%vhost%', vhost)
    tmpl = tmpl.replace('%vhosts%', ' '.join(vhosts))
    tmpl = tmpl.replace('%proxy_addr%', proxy_addr)
    tmpl = tmpl.replace('%ssl_cert%', ssl_cert)
    tmpl = tmpl.replace('%ssl_cert_key%', ssl_cert_key)

    wpath = os.path.join(CONF_DIR, f'{vhost}.conf')

    return write_file(wpath, tmpl)


def del_proxyconf(vhost):

    try:
        os.remove(os.path.join(CONF_DIR, f'{vhost}.conf'))
    except:
        return


def dinspect(id):
    dio = exec_cmd(f'docker container inspect {id}')
    return json.loads(dio)

def get_first_port(ports):
    fp = None
    for k in ports.keys():
        fp = k[0:k.index('/')]
        break

    return fp

def get_vhosts(env):
    r = None
    for var in env:
        x = re.search("^VIRTUAL_HOST=(.*)", var)
        if (x):
            vhost = x.group(1)
            r = vhost.split(',')
            break

    return r

def get_wantssl(env):
    for var in env:
        x = re.search("^WANT_SSL=", var)
        if (x):
            return True

    return False

def get_http_port(env):
    r = None
    for var in env:
        x = re.search("^HTTP_PORT=(.*)", var)
        if (x):
            r = x.group(1)
            break

    return r

def renew_le(vhost):
    exec_cmd(f'certbot certonly --webroot -w /tmp/letsencrypt -d {vhost} --agree-tos --email nobody@gmail.com -q')
    return

def update_le(vhost):

    cert, key = get_le(vhost)

    if (cert):
        d = read_file(cert)
        c = x509.load_pem_x509_certificate(d.encode('ascii'), default_backend())

        now = datetime.now()
        diff = (c.not_valid_after-now).days

        if (diff < 7):
            renew_le(vhost)
    else:
        renew_le(vhost)

    return

def conf_container(id, status=None):
    tj = dinspect(id)

    try:
        status = tj[0]['State']['Status'] if not status else status
        env = tj[0]['Config']['Env']
        hostname = tj[0]['Config']['Hostname']
        ports = tj[0]['Config']['ExposedPorts']
        networks = tj[0]['NetworkSettings']['Networks']
        ip = networks[list(networks.keys())[0]]['IPAddress']
    except:
        return

    httpp = get_http_port(env)
    fp = get_first_port(ports)
    vhosts = get_vhosts(env)
    wssl = get_wantssl(env)

    httpp = httpp if httpp else fp

    if (not httpp or not vhosts):
        return

    if (status == 'running' or status == 'start'):
        print(f'Proxying {vhosts[0]} [{ip}]')
        create_proxyconf(vhosts, hostname, httpp, ip)
        if (wssl):

            exec_cmd(f'nginx -s reload')
            time.sleep(10)
            update_le(vhosts[0])

            #recreate with LE certificates now
            create_proxyconf(vhosts, hostname, httpp, ip)

    else:
        print(f'Unproxying {vhosts[0]}')
        del_proxyconf(vhosts[0])

    exec_cmd(f'nginx -s reload')



def on_line(line):

    tj = json.loads(line)

    if (not tj or not 'id' in tj):
        return

    conf_container(tj['id'], tj['status'])


def dlisten():

    p = Popen(['docker', 'events', '--format', '{{json .}}', '--filter',
        'event=start', '--filter', 'event=kill'],
        stdout=PIPE, stderr=PIPE, stdin=PIPE)

    while (True):
        line = p.stdout.readline()
        if (not line):
            break

        on_line(line)


def setup():
    p = Popen(['docker', 'ps', '-a', '--format', '{{.ID}}'],
    stdout=PIPE, stderr=PIPE, stdin=PIPE)

    while (True):
        line = p.stdout.readline()
        if (not line):
            break

        #line = id
        conf_container(line[:-1].decode('utf-8'))

print('Started')
setup()
dlisten()
