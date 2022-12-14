import logging

"""
SalesforceSObject class
wrapper to contain outputs of Salesforce SObject query
"""
class SalesforceSobject:

    def __init__(self, name, urls, env, fields):
        self.name = name
        self.urls = urls
        self.env = env
        self.fields = fields
        self.logger = logging.getLogger(__name__)
        self.logger.debug('%s initiated with object name, %s ',__name__, self.name)
        self.logger.debug('URLS, %s', self.urls)
