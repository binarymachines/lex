#!/usr/bin/env python

import json
import uuid
from snap import common
from mercury.dataload import DataStore
from mercury.mlog import mlog, mlog_err


class ObjectFactory(object):
    
    @classmethod
    def create_db_object(cls, table_name, db_svc, **kwargs):
        DbObject = getattr(db_svc.Base.classes, table_name)
        return DbObject(**kwargs)


def to_boolean(value: str):

    if not value:
        return False
    
    if value.lower() == 'yes':
        return True
    
    if value.lower() == 'no':
        return False


class PostgresDatastore(DataStore):

    def __init__(self, service_object_registry, *channels, **kwargs):
        super().__init__(service_object_registry, *channels, **kwargs)


    def write_permit_data(self, record, db_service, **write_params):

        new_id = None

        {
            "application": "SX2019010440",
            "date": "8/15/2019",
            "is_renewal": "Yes",
            "status": "Approved",
            "type": "SX"
        }
        
        olap = self.service_object_registry.lookup('olap')

        
        permit_type_id = olap.dim_id_for_value('dim_permit_type', record['type'])
        
        date_tokens = record['date'].split('/')

        if len(date_tokens) != 3:
            raise Exception(f'bad date format {record["date"]}')

        date_month = date_tokens[0]
        date_day = date_tokens[1]
        date_year = date_tokens[2]

        day_id = olap.dim_id_for_value('dim_date_day', int(date_day))
        month_id = olap.dim_id_for_value('dim_date_month', int(date_month))
        year_id = olap.dim_id_for_value('dim_date_year', int(date_year))

        with db_service.txn_scope() as session:

            permit_data = {
                'id': str(uuid.uuid4()),
                'app_id': record['application'],
                'is_renewal': to_boolean(record['is_renewal']),
                'application_date': record['date'].replace('/', '-'),
                'type_id': permit_type_id,
                'status': record['status'],
                'date_day_id': day_id,
                'date_month_id': month_id,
                'date_year_id': year_id
            }
            
            db_rec = ObjectFactory.create_db_object('fact_permit', db_service, **permit_data)
            session.add(db_rec)
            session.flush()
            new_id = str(db_rec.id)

        return new_id
    

    def write(self, records, **write_params):

        postgres_svc = self.service_object_registry.lookup('postgres')        
        for raw_rec in records:

            rec = json.loads(raw_rec)
            try:
                
                id = self.write_permit_data(rec, postgres_svc)
                
            except Exception as err:
                mlog_err(err, issue=f"Error ingesting permit record.", record=rec)

     

