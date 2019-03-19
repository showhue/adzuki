from abc import abstractmethod
from . import EntityWrapper
from google.cloud import datastore
from random import random

class Model(object):
  def __init__(self):
    self._client = datastore.Client(project=self.project, namespace=self.namespace)

  @property
  @abstractmethod
  def project(self):
    pass

  @property
  @abstractmethod
  def namespace(self):
    pass

  @property
  @abstractmethod
  def kind(self):
    pass

  @property
  @abstractmethod
  def attributes(self):
    pass

  def get(self, entity_id):
    key = self._client.key(self.kind, entity_id)
    entity = self._client.get(key)
    return None if entity == None else EntityWrapper(self, entity)

  def put(self, entity):
    return self._client.put(entity)

  def create(self, entity_id, overwrite=False):
    if self.existed(entity_id):
      raise KeyError('Key\'%s\' existed, to overwrite please set overwrite=True.')
    else:
      key = self._client.key(self.kind, entity_id)
      entity = datastore.Entity(key=key)
      return EntityWrapper(self, entity)

  def existed(self, entity_id):
    entity = self.get(entity_id)
    return entity is not None

  def query(self, filters=[], distinct_on=[], projection=[], limit=None, offset=0, shuffle=False, postprojection=None):
    query = self._client.query(kind=self.kind)
    if len(distinct_on) > 0:
      query.distinct_on = distinct_on
    if len(projection) > 0:
      query.projection = projection
    if shuffle:
      query.add_filter('random_key', '>=', random())
      query.order.append('random_key')
    for column, operator, value in filters:
      query.add_filter(column, operator, value)
    entities = query.fetch(limit=limit, offset=offset)
    wrapped = list(EntityWrapper.from_iterator(self, entities, postprojection))
    if shuffle and limit is not None and len(wrapped) < limit:
      circular_wrapped = self.query(filters, distinct_on, projection, limit=limit - len(wrapped))
      return list(set(wrapped) | set(circular_wrapped))
    else:
      return wrapped