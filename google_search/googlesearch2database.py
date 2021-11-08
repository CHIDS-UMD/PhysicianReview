import os
import numpy as np
import pandas as pd
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Table, Text, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from datetime import datetime


folder = 'Output'
files = [os.path.join(folder, i) for i in os.listdir(folder) if '.p' in i]
files.sort()
newName2Cols = {
    'NPI':'NPI', 
    'URLs': 'searched_urls', 
    'CltTime':'clct_time',
}


def get_clean_row_data(row, newName2Cols):
    new_row = {}
    for newname, cols in newName2Cols.items():
        new_row[newname] = row[cols]  
    new_row2 = {}
    for k, v in new_row.items():
        if v == None:
            continue
        elif 'Time' in k:
            new_row2[k] = pd.to_datetime(v)
        elif type(v) == list:
            new_row2[k] = json.dumps(v)
        else:
            new_row2[k] = v
    return new_row2

def sdb_connect(basedir, name = 'NEEPS'):
    return create_engine('sqlite:///'+os.path.join(basedir, name + '.sqlite'))

def mdb_connect():
    MySQL_DB = 'mysql+pymysql://root:@localhost:3306/physicianinfo?charset=utf8'
    return create_engine(MySQL_DB)

Base = declarative_base()

def create_table(engine):
    Base.metadata.create_all(engine)

    
class GoogleSearch(Base):
    __tablename__ = 'GoogleSearch'
    id = Column(Integer, primary_key=True)
    NPI = Column(Integer)
    URLs = Column(Text)
    CltTime = Column(DateTime)
    
engine = mdb_connect()
create_table(engine)
Session = sessionmaker(bind = engine)
session = Session()
total_phy = 0

for file in files:
    Data = pd.read_pickle(file)
    print(file)
    for idx, row in Data.iterrows():
        # row
        new_row = get_clean_row_data(row, newName2Cols)
        
        npi_row = GoogleSearch(**new_row)  
        session.add(npi_row)
        total_phy += 1
        if idx % 1000 == 0:
            print(idx, total_phy, datetime.now())  
    print('commit...')
    session.commit()