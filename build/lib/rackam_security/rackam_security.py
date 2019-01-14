# -*- coding: utf-8 -*-
"""
Created on Tue May 12 13:40:03 2015

@author: guillaume.pealat
"""
import json
import pandas as pd
import types

# -*- coding: utf-8 -*-
class rackam_security():
    _datastore = None
    _uid = None

    def __init__(self, env, uid):
        self._datastore = env
        self._uid = uid
        
        #When the underlying is created we need to load the metafunction dictionary
        #self._metafunction_dict = self._datastore.getMetaFunction(self._uid)
        
        self._metadata_dict = self._datastore.getMetadata(self._uid)
    
    
    def getUID(self):
        return self._uid
        
    def registerMetaFunction(self, fnct_label, fnct):
        #self._metafunction_dict = {}
        self._metafunction_dict[fnct_label] = types.MethodType(fnct,self)
        self._datastore.saveMetaFunction(self._uid, self._metafunction_dict)
        
    def applyMetaFunction(self, metafunction_name, **kwargs):
        return self._metafunction_dict[metafunction_name](**kwargs)
    
    def getMetadata(self):
        return self._datastore.getMetadata(self._uid)
        
    def getToDate(self):
        return self._datastore.getSecurityToDate(self._uid)
        
    def describe(self):      
        #We get the metadata stored in the DB
        metadata_dict = self._datastore.getMetadata(self._uid)

        #We get the identifier list from the DB        
        identifier_dict = self._datastore.getIdentifiers(self._uid)
        
        id_dict = {'identifiers':identifier_dict}
        
        #We have to concatenate the data
        #merged_dict = {key: value for (key, value) in (id_dict.items() + metadata_dict.items())}
        merged_dict = {key: value for (key, value) in (metadata_dict.items())}
        
        #We prettyprint them
        print(json.dumps(merged_dict, indent=4, sort_keys=True))
 
    def addMetadata(self, metadata_dict):
        #We check that the function argument is indeed a dict
        if not isinstance(metadata_dict, dict):
            raise TypeError('Input should be a dictionary')

        #First we get the actual metadata
        data_json = self._datastore.getMetadata(self._uid)

        #We check if the key of the new dictionary does not exist
        for k in metadata_dict.keys():        
            if data_json.has_key(k):
                #We have to remove the old key to replace by the new key
                data_json[k]=metadata_dict[k]

        #We have to concatenate the data
        merged_dict = {key: value for (key, value) in (data_json.items() + metadata_dict.items())}
        
        #We transform the merged dictionary into a merged JSON before updating the metadata        
        merged_json = json.dumps(merged_dict)
        
        #we can now store the data
        self._datastore.saveMetadata( self._uid, merged_json)
    
    def getData(self, data_list = None):
        #function to load the raw data for a security
    
        data = self._datastore.getSecurityData(self._uid)
        
        if data_list == None:
            return data
        else:
            #Build the intersection of the keys from the data in DB and the list passed
            intersect = set(data.keys()) & set(data_list)
            #Return a dictionnary of the data requested
            return {x:data[x] for x in intersect}
        
    def saveData(self, raw_data_df, data_name, concat = True):
        #We check that the function argument is indeed a dict
        if not isinstance(raw_data_df, pd.core.frame.DataFrame) :
            raise TypeError('Input should be a Pandas DataFrame')
        
        #First step is to load the actual data saved in the DB   

        data_in_db = self.getData()
        
        if not data_in_db:
            
            #Dict is empty so there is no data in DB
            data_new = {}
            data_new[data_name]=raw_data_df.sort_index(ascending=True, axis=1)
            
            self._datastore.updateSecurityData(self._uid, data_new)
            
        elif not data_name in data_in_db.keys():
            #This key is not in the DB already
            data_in_db[data_name]=raw_data_df.sort_index(ascending=True, axis=1)

            self._datastore.updateSecurityData(self._uid, data_in_db)
            
        else:
            if concat:
                #We concatenate the 2 dataframes               
                data_in_db[data_name] = pd.concat([data_in_db[data_name],raw_data_df]).sort(ascending=True)

            else:
                #We fully replace the old dataframe by the new one
                data_in_db[data_name] = raw_data_df.sort_index(ascending=True, axis=1)
        
            self._datastore.updateSecurityData(self._uid, data_in_db)
            
