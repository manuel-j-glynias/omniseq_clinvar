#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 06:07:58 2019

@author: mglynias
"""

from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import urllib.parse
import logging
import sys


app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('calling MongoClient')
client = MongoClient('localhost', 27017)
try:
    # inexpensive way to determine if mongo is up, if not then exit
    client.admin.command('ismaster')
except ConnectionFailure:
    logger.critical("Server not available, exiting")
    sys.exit()

db = client.omniseq


@app.route('/')
def index():
    myDict = {'explain':'Server Works!'}
    return jsonify(myDict)
  

def is_oncogene(gene):
    mycol = db["gene_categories"]
    myquery = { 'gene':gene }
    mydoc = mycol.find_one(myquery)
    b = False
    if mydoc!= None:
        if mydoc['category'] == 'Oncogene':
            b = True
    return b
        
    

@app.route("/omniseq_api/v1/shouldReport/", methods=['GET'])
def handle_shouldReport():
    myDict = {'explain':'Error!'}
    gene = request.args.get('gene', None) # use default value repalce 'None'
    pdot = request.args.get('pDot', None)
    if (gene != None and pdot != None):
        mycol = db["clinvar"]
        myquery = { 'gene':gene, 'pDot':pdot}
        mydoc = mycol.find_one(myquery)
        # We want to report any oncogene variant not found in ClinVar
        if (mydoc == None):
            # is this an oncogene?
            if is_oncogene(gene):
                myDict = {'shouldReport':True, 'explain': 'pDot not found in ClinVar, and gene is oncogene'}
            else:
                myDict = {'shouldReport':False, 'explain': 'pDot not found in ClinVar, and gene not oncogene'}
        else:
            myDict = {'shouldReport':mydoc['is_majority_vote_not_benign'], 'explain': mydoc['explain'], 'variant_id' : mydoc['variant_id']}

    return jsonify(myDict)




    
    
if __name__ == "__main__":
    app.run(host='0.0.0.0')
    