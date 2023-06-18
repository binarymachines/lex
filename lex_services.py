#!/usr/bin/env python

import os, sys
import json
from json.decoder import JSONDecodeError
from snap import snap, common

from collections import namedtuple
from contextlib import contextmanager
import datetime
import time

import sqlalchemy as sqla
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy_utils import UUIDType

from mercury.mlog import mlog, mlog_err
import uuid

import psycopg2


POSTGRESQL_SVC_PARAM_NAMES = ["host", "port", "dbname", "username", "password"]



class PostgreSQLService(object):
    def __init__(self, **kwargs):
        kwreader = common.KeywordArgReader(*POSTGRESQL_SVC_PARAM_NAMES)
        kwreader.read(**kwargs)

        self.db_name = kwargs["dbname"]
        self.host = kwargs["host"]
        self.port = int(kwargs.get("port", 5432))
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.schema = kwargs.get("schema", "public")
        self.metadata = None
        self.engine = None
        self.session_factory = None
        self.Base = None
        self.url = None

        url_template = "{db_type}://{user}:{passwd}@{host}:{port}/{database}"
        db_url = url_template.format(
            db_type="postgresql+psycopg2",
            user=self.username,
            passwd=self.password,
            host=self.host,
            port=self.port,
            database=self.db_name,
        )

        retries = 0
        connected = False
        while not connected and retries < 3:
            try:
                self.engine = sqla.create_engine(db_url, echo=False)
                self.metadata = MetaData(schema=self.schema)
                self.Base = automap_base()
                self.Base.prepare(self.engine, reflect=True)
                self.metadata.reflect(bind=self.engine)
                self.session_factory = sessionmaker(
                    bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
                )

                # this is required. See comment in SimpleRedshiftService
                connection = self.engine.connect()
                connection.close()
                connected = True
                mlog("+++ Connected to PostgreSQL DB.")
                self.url = db_url

            except Exception as err:
                print(err, file=sys.stderr)
                print(err.__class__.__name__, file=sys.stderr)
                print(err.__dict__, file=sys.stderr)
                time.sleep(1)
                retries += 1

        if not connected:
            raise Exception(
                "!!! Unable to connect to PostgreSQL db on host %s at port %s."
                % (self.host, self.port)
            )

    @contextmanager
    def txn_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def connect(self):
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()


LOOKUP_SVC_PARAM_NAMES = [
    'table_name',
    'key_columns'
]


class OLAPDimensionSvc(object):
    def __init__(self, **kwargs):

        self.pg_svc = PostgreSQLService(**kwargs)
        self.dimensions_by_value = {}
        self.dimensions_by_label = {}

        for tbl_name in kwargs['dimension_tables']:
            self.dimensions_by_value[tbl_name] = self.load_dimension_values(tbl_name, self.pg_svc)

        for tbl_name in kwargs['dimension_tables']:
            self.dimensions_by_label[tbl_name] = self.load_dimension_labels(tbl_name, self.pg_svc)

        mlog('+++ OLAP dimensions loaded:', tables=[key for key in kwargs['dimension_tables']])


    def load_dimension_values(self, table_name, db_svc):
        dim_data = {}
        data_object = getattr(db_svc.Base.classes, table_name)

        with db_svc.txn_scope() as session:
            resultset = session.query(data_object).all()

            for record in resultset:
                dim_data[str(record.value)] = (record.id, record.label)

        return dim_data


    def load_dimension_labels(self, table_name, db_svc):

        dim_data = {}
        data_object = getattr(db_svc.Base.classes, table_name)

        with db_svc.txn_scope() as session:
            resultset = session.query(data_object).all()

            for record in resultset:
                dim_data[record.label] = (record.id, record.value)

        return dim_data


    def dim_id_for_value(self, dim_table_name, value):
        rltuple = self.dimensions_by_value[dim_table_name][str(value)]
        return rltuple[0]
    

    def dim_id_for_label(self, dim_table_name, label):
        rltuple = self.dimensions_by_label[dim_table_name][str(label)]
        return rltuple[0]


    def dim_label_for_value(self, dim_table_name, value):
        rltuple = self.dimensions_by_value[dim_table_name][str(value)]
        return rltuple[3]
    
    
    def get_dim_ids_for_timestamp(self, source_timestamp) -> dict:

        datestamp = datetime.datetime.fromtimestamp(int(source_timestamp))

        data = {}
        data['second'] = self.dim_id_for_value('dim_time_second', datestamp.minute)
        data['minute'] = self.dim_id_for_value('dim_time_minute', datestamp.minute)
        data['hour'] =  self.dim_id_for_value('dim_time_hour', datestamp.hour)
        data['day'] = self.dim_id_for_value('dim_date_day', datestamp.day)
        data['month'] = self.dim_id_for_value('dim_date_month', datestamp.month)
        data['year'] = self.dim_id_for_value('dim_date_year', datestamp.year)
        
        return data


class PGObjectLookupSvc(object):
    def __init__(self, **kwargs):
        
        self.pg_svc = PostgreSQLService(**kwargs)

        # TODO: do this for all service objects

        kwreader = common.KeywordArgReader(*LOOKUP_SVC_PARAM_NAMES)
        kwreader.read(**kwargs) # TODO: possibly rename this to validate()  
        
        self.table_name = kwargs['table_name']
        key_columns = kwargs['key_columns']
        self.lookup_tbl = dict()

        with self.pg_svc.txn_scope() as session:
            data_object = getattr(self.pg_svc.Base.classes, self.table_name)
            resultset = session.query(data_object).all()

            for record in resultset:
                key = self.compose_key(record, *key_columns)
                self.lookup_tbl[str(key)] = record

    
    def compose_key(self, record, *key_columns):
        key_tokens = []
        for kc in key_columns:
            key_tokens.append(str(getattr(record, kc)))

        return '%'.join(key_tokens)


    def find(self, *values):

        key = '%'.join(values)
        return self.lookup_tbl.get(key)
    

    def update(self, record: object, *key_columns):
        key = self.compose_key(record, *key_columns)
        self.lookup_tbl[str(key)] = record
        

        