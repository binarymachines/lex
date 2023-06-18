#!/usr/bin/env python

import json
from snap import common
from mercury.dataload import DataStore
from mercury.mlog import mlog, mlog_err


class ObjectFactory(object):
    
    @classmethod
    def create_db_object(cls, table_name, db_svc, **kwargs):
        DbObject = getattr(db_svc.Base.classes, table_name)
        return DbObject(**kwargs)


class PostgresDatastore(DataStore):

    def __init__(self, service_object_registry, *channels, **kwargs):
        super().__init__(service_object_registry, *channels, **kwargs)


    

    def write_permit_data(self, record, db_service, **write_params):
        
        with db_service.txn_scope() as session:

            permit_data = {
                
            }
            
            #new_brand = ObjectFactory.create_db_object('brands', db_service, **brand_data)
            #session.add(new_brand)


    def write(self, records, **write_params):

        postgres_svc = self.service_object_registry.lookup('postgres')        
        for raw_rec in records:

            rec = json.loads(raw_rec)
            try:
                mlog('DB insert placeholder')
                #self.write_borderxlab_data(rec, postgres_svc)
                #mlog('wrote record to database', id=rec['id'])

            except Exception as err:
                mlog_err(err, issue=f"Error ingesting {record_type} record.", record=rec)

     

