# -*- coding: utf-8 -*-

import psycopg2
from rackam_security import rackam_security

import json
import lz4
from datetime import datetime
import dill
import contextlib

connection_data = {'LIVE':{'host':'localhost','port':5432,'user':'postgres','pwd':'password','db':'rackam'}}

class rackam_datastore():
    #_db_connection = None
    _db_environment = None
    
    def __init__(self, env):
        #Add the check that the input are in the correct format
    
        self._db_environment = env        
        
        connection_string = "host=%s dbname=%s user=%s password=%s" %(connection_data[self._db_environment]['host'],connection_data[self._db_environment]['db'],connection_data[self._db_environment]['user'],connection_data[self._db_environment]['pwd'])
        
        self._db_connection = psycopg2.connect(connection_string, async=0)
           
    def __del__(self):
        self._db_connection.close()
    
    def closedatastore(self):
        self._db_connection.close()
        
    def list_securities(self):
    
        query = "SELECT identifiers FROM security_master"
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            data = curs.fetchall()
        
        return_data = []
        
        for record in data:
            #return_data.append(json.loads(record[0],encoding='str'))
            #return_data.append(yaml.safe_load(record[0]))  
            #print(record[0])
            #return_data.append(json.laods(record[0])) 
            return_data.append(record[0]) 
            
        return return_data

    def createSecurity(self, identifier_dict, metadata_dict={}, livedate = datetime(1900,1,1,9,00,00)):
        #Check if the input is a dictionary
        if not isinstance(identifier_dict, dict):
            raise TypeError('The identifier input should be a dictionary')

        #if not isinstance(metafunction_dict, dict):
        #    raise TypeError('The metafunction input should be a dictionary')
            
        #We need first to create the JSON for the identifiers
        json_dic = json.dumps(identifier_dict)
        
        #We create the dictionnary for the metadata
        meta_json_dict = json.dumps(metadata_dict)
        

        #Add the creation of an empty dictionnary for the data      
        #serialized_metafunction = dill.dumps(metafunction_dict)
        serialized_metafunction = lz4.block.compress(dill.dumps({}))
        
        query = "INSERT INTO security_master(identifiers, livedate, metadata, metafunction) VALUES (%s,%s,%s,{}) RETURNING uid" . format(psycopg2.Binary(serialized_metafunction))
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query,(json_dic, livedate, meta_json_dict))
            local_uid = curs.fetchone()[0]

        data = {}      
        serialized_data = lz4.block.compress(dill.dumps(data))
        
        query = "INSERT INTO security_data(uid, data) VALUES ({}, {})" . format( local_uid, psycopg2.Binary(serialized_data))
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            
        self._db_connection.commit()
        
        return 
        
    def getSecurity(self, identifier):
        #Check if the input is a dictionary
        if not isinstance(identifier, dict):
            raise TypeError('Input should be a dictionary')
            
        #if the identifier has an id, this superseeds everything
        if 'id' in identifier:
            #We will load the uid in order to create the security object
            query = "SELECT uid FROM security_master WHERE uid = {};" . format(identifier['id'])
        else:
            #Check if there is a key called 'identifier'
            if 'identifier' not in identifier.keys():
                raise KeyError('A key should be called identifier')
            #Check if there is a key called 'value'
            if 'value' not in identifier.keys():
                raise KeyError('A key should be called value')
            
            #We will load the uid in order to create the security object
            query = "SELECT uid FROM security_master WHERE identifiers->>'{}' = '{}';" . format(identifier['identifier'], identifier['value'])
            
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            data = curs.fetchone()
            
        #Add the check that there is something returned eventually
        #if isinstance(data, None):
        #    raise ValueError('The security has not been found')
            
        uid = int(data[0])
        
        return rackam_security.rackam_security(self, uid)
        
    def getMetadata(self, uid):
        try:
            query = "SELECT metadata FROM security_master WHERE uid = {}" . format(uid)
            
            with contextlib.closing(self._db_connection.cursor()) as curs:
                curs.execute(query)
                data = curs.fetchone()
        
            #Data are stored as JSON string, so we need to load them    
            #data_json = json.loads(data)
            data_json = data[0]
            
            return data_json
        except:
            print("Exception")

    def getIdentifiers(self, uid):
        query = "SELECT identifiers FROM security_master WHERE uid = {}"
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query . format(uid))
            data = curs.fetchone()
            
        #Data are stored as JSON string, so we need to load them    
        #data_json = json.loads(data[0])
        data_json = data[0]
        
        return data_json
        
    def saveMetadata(self, uid, metadata_json):
        try:
            
            
            if self._db_connection.status == psycopg2.extensions.STATUS_SETUP:
                raise Exception('CONNECTION ERROR')
                
                query = "UPDATE security_master SET metadata = %s WHERE uid = %s"
        
            with contextlib.closing(self._db_connection.cursor()) as curs:
                curs.execute(query,(metadata_json, str(uid)))
        
            self._db_connection.commit()
        except:
            print("Connection with the datastore is lost")
            
    def getSecurityFromMetadata(self, metadata_query, asofdate = datetime.now()):
        #Check if the input is a dictionary
        if not isinstance(metadata_query, dict):
            raise TypeError('Input should be a dictionary')
            
        #We will load the uid in order to create the security object
        query = "SELECT uid FROM security_master WHERE metadata->>%s = %s AND livedate <= '{}';" . format(asofdate)
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query, (metadata_query.keys()[0], metadata_query[metadata_query.keys()[0]]))
            data = curs.fetchall()        
 
        security_list = []
        
        for row in data:
            security_list.append(rackam_security.rackam_security(self, row[0]))
        
        return security_list
    
    def getSecurityData(self, uid):
    #try:
        if self._db_connection.status == psycopg2.extensions.STATUS_SETUP:
            raise Exception('CONNETION ERROR')
 
        query = "SELECT data FROM security_data WHERE uid = {}" . format(uid)
                  
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            #compressed_data = str(curs.fetchone()[0])
            compressed_data = curs.fetchone()[0]
            print(type(compressed_data))
               
        if compressed_data == None:
            raise KeyError('There is no result for the query')
        
        #We need to decompress the data
        data = dill.loads(lz4.block.decompress(compressed_data))
        
        
        return data
    #except:
        print("Connection with the datastore is lost")
    
    def getSecurityToDate(self, uid):
 
        query = "SELECT todate FROM security_master WHERE uid = {}" . format(uid)
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            data = str(curs.fetchone()[0])
               
        if data == None:
            raise KeyError('There is no result for the query')
        
        return data

        print("Connection with the datastore is lost")
           
    def saveSecurityData(self, uid, raw_data):
        try:
            if self._db_connection.status == psycopg2.extensions.STATUS_SETUP:
                raise Exception('CONNECTION ERROR')
         
            #We compress the data
            compressed_raw_data = lz4.block.compress(dill.dumps(raw_data))
            
            #Function that saves the input raw_data (dict) into the DB (lz4 compressed)      
            query = "INSERT INTO security_data(data, uid) VALUES(%s,%s)"
    
            with contextlib.closing(self._db_connection.cursor()) as curs:
                curs.execute(query, (psycopg2.Binary(compressed_raw_data), str(uid)))
            
            self._db_connection.commit()
        except:
            print("Connection with the datastore is lost")
            
    def updateSecurityData(self, uid, raw_data):
        #We compress the data
        compressed_raw_data = lz4.block.compress(dill.dumps(raw_data))
        
        #Function that saves the input raw_data (dict) into the DB (lz4 compressed)      
        query = "UPDATE security_data set data = {} WHERE uid = {}" . format(psycopg2.Binary(compressed_raw_data), str(uid))
 
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
        
        self._db_connection.commit()
        
        return

    def saveMetaFunction(self, uid, data):
        #We compress the data
        dilled_data = lz4.block.compress(dill.dumps(data))
        #Function that saves the input raw_data (dict) into the DB (lz4 compressed)      
        query = "UPDATE security_master SET metafunction = {} WHERE uid = {}" . format(psycopg2.Binary(dilled_data), str(uid))
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
        
        self._db_connection.commit()

    def getMetaFunction(self, uid):
        query = "SELECT metafunction FROM security_master WHERE uid = {}". format(uid)
        
        with contextlib.closing(self._db_connection.cursor()) as curs:
            curs.execute(query)
            compressed_data = str(curs.fetchone()[0])

        
        data = dill.loads(lz4.block.decompress(compressed_data))
        
        return data