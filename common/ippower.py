#!/usr/bin/env python
#
# Fencing driver for the IP Power 9258 remote power switch.

import re
import sys
import httplib
import time

from datetime import datetime, timedelta
from httplib import HTTPConnection
from optparse import OptionParser

re_html = re.compile('<.*?>')


class Error(Exception):
    """Fencing error."""


class Options(object):
    """Class to store command-line options."""
    ipaddr = '10.238.16.151'
    login = 'admin'
    passwd = '12345678'
    port = 80
    option = 'reboot'
    delay = 1
    debug = False


def ip9258_rpc(opts, cmd, args=[]):
    """Execute a remote procedure call on the IP9258. Returns the HTTP
    response object.
    """
    # The IP9258 requires the URL arguments to be in a specified order.
    conn = HTTPConnection(opts.ipaddr)
    headers = {}
    creds = '%s:%s' % (opts.login, opts.passwd)
    headers['Authorization'] = 'Basic %s' % creds.encode('base64')
    url = '/Set.cmd?CMD=%s' % cmd
    url += ''.join(['+%s=%s' % (k, v) for k,v in args ])
    try:
        conn.request('GET', url, headers=headers)
    except:
        return "Exception on conn.request"
    return conn.getresponse()


def set_power(opts, port, enable):
    """Set power on port `port' to `enable'."""
    args = []
    args.append(('P%d' % (59 + port), '%d' % bool(enable)))
    response = ip9258_rpc(opts, 'SetPower', args)
    if response.status != httplib.OK:
        m = '"SetPower" RPC returned status %d.' % response.status
        raise Error, m


def get_power(opts, port=None):
    """Get power status of port `port'."""
    response = ip9258_rpc(opts, 'GetPower')
    if response.status != httplib.OK:
        m = '"GetPower" RPC returned status %d.' % response.status
        raise Error, m
    html = response.read()
    text = re_html.sub('', html)
    print 'get_power -> text:', text ## to debug why it failed to parse 
    try:
        tuples = [ s.split('=') for s in text.split(',') ]
        status = dict(((int(t[0][1:]) - 59, bool(int(t[1]))) for t in tuples))
    except ValueError:
        m = 'Could not parse output of "GetPower" RPC.'
        raise Error, m
    if port:
        return status[port]
    else:
        return status

def reboot(opts, port):
    """Reboot the port `port'."""
    # Reboot is a power off + power on. But as we may be fencing
    # ourselves, we need to schedule the power on event as we may not be
    # there anymore.
    response = ip9258_rpc(opts, 'GetTime')
    html = response.read()
    text = re_html.sub('', html).strip()
    print 'get_power -> text:', text ## to debug why it failed to parse 
    try:
        dt = datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        m = 'Could not parse output of "GetTime" RPC.'
        raise Error, m
    dt += timedelta(seconds=10 + opts.delay)  # add 10 secs for safety
    args = []
    args.append(('Power', '%dA' % port))
    args.append(('YY', '%04d' % dt.year))
    args.append(('MM', '%02d' % dt.month))
    args.append(('DD', '%02d' % dt.day))
    args.append(('HH', '%02d' % dt.hour))
    args.append(('MN', '%02d' % dt.minute))
    args.append(('SS', '%02d' % dt.second))
    args.append(('PARAM', '128'))  # 128 means one shot
    args.append(('ONOFF', '1'))
    response = ip9258_rpc(opts, 'SetSchedule', args)
    if response.status != httplib.OK:
        m = '"SetSchedule" RPC returnd status %d.' % response.status
        raise Error, m
    set_power(opts, port, False)

