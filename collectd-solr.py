#!/usr/bin/env python
#
# Collectd plugin for collecting solr container stats


import collectd
import requests, socket


SOLR_HOST = 'localhost'
SOLR_PORT = 8983
SOLR_STATUS = 'OVERSEERSTATUS'
SOLR_INTERVAL = 1
VERBOSE_LOGGING = True


# setup logging
def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('solr_info plugin [verbose]: %s' % msg)


class Solr(object):
    def __init__(self, host='localhost', port=8983, status='OVERSEERSTATUS'):
        self.host = host
        self.port = port
        self.status = status


    def get_status(self, host=SOLR_HOST, port=SOLR_PORT, status=SOLR_STATUS):
        """Execute to Solr status command and return JSON object"""
        url = 'http://{}:{}/solr/admin/collections?action={}&wt=json'.format(SOLR_HOST, SOLR_PORT, SOLR_STATUS)
        try:
            r = requests.get(url)
            if r.status_code == 200:
                reply = r.json()
        except Exception as e:
            log_verbose('collectd-solr plugin: can\'t get {} info, with error message {}'.format(status, e.message))
        return reply


    def get_leader(self):
        return 1 if socket.gethostname() in self.get_status()[u'leader'] else 0

    def get_overseer_queue_size(self):
        return self.get_status()[u'overseer_queue_size']


    def get_overseer_work_queue_size(self):
        return self.get_status()[u'overseer_work_queue_size']


    def get_overseer_collection_queue_size(self):
        return self.get_status()[u'overseer_collection_queue_size']


class SolrPlugin(object):
    def configure_callback(self, conf):
        """Receive configuration block"""
        global SOLR_HOST, SOLR_PORT, SOLR_STATUS
        for node in conf.children:
            if node.key == 'Host':
                SOLR_HOST = node.values[0]
            elif node.key == 'Port':
                SOLR_PORT = int(node.values[0])
            elif node.key == 'Status':
                SOLR_STATUS = node.values[0]
            elif node.key == 'Interval':
                SOLR_INTERVAL = int(float(node.values[0]))
            else:
                collectd.warning('collectd-solr plugin: Unknown config key: {}.'.format(node.key))
        log_verbose('Configured: host={}, port={}, status={}, interval={}'.format(SOLR_HOST, SOLR_PORT, SOLR_STATUS, SOLR_INTERVAL))


    def dispatch_value(self, instance, value, value_type):
        val = collectd.Values(plugin='solr')
        val.plugin_instance = instance
        val.type = value_type
        val.values = [value]
        val.dispatch()


    def read_callback(self):
        log_verbose('solr-info plugin: Read callback called')
        solr = Solr(SOLR_HOST, SOLR_PORT, SOLR_STATUS)
        self.dispatch_value('leader', solr.get_leader(), 'gauge')
        self.dispatch_value('overseer_queue_size', solr.get_overseer_queue_size(), 'gauge')
        self.dispatch_value('overseer_work_queue_size', solr.get_overseer_collection_queue_size(), 'gauge')
        self.dispatch_value('overseer_collection_queue_size', solr.get_overseer_collection_queue_size(), 'gauge')


# register callbacks
plugin = SolrPlugin()
collectd.register_config(plugin.configure_callback)
collectd.register_read(plugin.read_callback, SOLR_INTERVAL)