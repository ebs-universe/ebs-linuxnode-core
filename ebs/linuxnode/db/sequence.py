

import os
from twisted import logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


class GenericSequencePersistenceManager(object):
    _db_name = 'generic'
    _db_model = None
    _db_metadata = None

    def __init__(self, actual):
        self._actual = actual
        self._items = []
        self._is_loaded = False
        self._log = None

        self._db_engine = None
        self._db = None
        self._db_dir = None
        _ = self.db

    @property
    def log(self):
        if not self._log:
            self._log = logger.Logger(
                namespace="{0}.pm".format(self._db_name),
                source=self
            )
        return self._log

    def get(self, reload=True):
        self._persistence_load(force=reload)
        return self._items

    def update(self, items):
        self._is_loaded = False
        self.clear()
        if not len(items):
            return
        session = self.db()
        self.log.debug("Inserting Items to DB '{}'"
                       "".format(self._db_name))
        try:
            for idx, item in enumerate(items):
                robj = self._db_model(idx, item)
                self._insert_item(idx, item)
                session.add(robj)
            session.commit()
            session.flush()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def _insert_item(self, seq, item):
        pass

    def _clear_item(self, item):
        pass

    def clear(self):
        self._is_loaded = False
        session = self.db()
        self.log.debug("Clearing Persistent Items from DB '{}'"
                       "".format(self._db_name))
        try:
            results = self.db_get_resources(session).all()
        except NoResultFound:
            session.close()
            return
        try:
            for robj in results:
                session.delete(robj)
                self._clear_item(robj)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def _persistence_load(self, force=False):
        if self._is_loaded and not force:
            return
        self.log.debug("Loading Persistent Items from DB '{}'"
                       "".format(self._db_name))
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        except NoResultFound:
            session.close()
            self._items = []
        try:
            _items = []
            for robj in results:
                _items.append(robj.native())
        finally:
            session.close()
        self._items = _items
        self.log.debug("Got {} Items from DB '{}'."
                       "".format(len(self._items), self._db_name))

    def db_get_resources(self, session, seq=None):
        q = session.query(self.db_model)
        if seq is not None:
            q = q.filter(
                self.db_model.seq == seq
            )
        else:
            q = q.order_by(self.db_model.seq)
        return q

    @property
    def db_model(self):
        if not self._db_model:
            raise AttributeError("_db_model Needs to be specified")
        return self._db_model

    @property
    def db_metadata(self):
        if not self._db_metadata:
            raise AttributeError("_db_metadata needs to be provided")
        return self._db_metadata

    @property
    def db(self):
        if self._db is None:
            self._db_engine = create_engine(self.db_url)
            self.db_metadata.create_all(self._db_engine)
            self._db = sessionmaker(expire_on_commit=False)
            self._db.configure(bind=self._db_engine)
        return self._db

    @property
    def db_url(self):
        return 'sqlite:///{0}'.format(
            os.path.join(self.db_dir, "{}.db".format(self._db_name))
        )

    @property
    def db_dir(self):
        return self._actual.db_dir

    def render(self):
        print("----------")
        print("{} DB Content".format(self._db_name))
        print("----------")
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        finally:
            session.close()
        print(results)
        print("----------")
