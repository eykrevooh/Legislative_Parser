import os, sys, time
import importlib
import datetime
import urllib, json
from bs4 import BeautifulSoup

from app.logic.sentiment import callChain
from app.logic.parse_sections import *
from app.logic.bill_scrapping import *
from app.models import *

def get_tweet(url):
    r = urllib.urlopen(url)
    soup = BeautifulSoup(r, 'html.parser')
    full_sum = soup.find("div", {"id": "libraryofcongress"})
    [s.extract() for s in full_sum('script')]
    count = 0
    result = []
    length = len(soup.find_all('p'))-20
    for p in (soup.find_all('p')):
        if count >= 7 and count <= length: 
            result.append(p.get_text())
        count += 1
    tweet =  "".join(result)[0:140]
    if tweet == "":
        tweet = "N/A"
    return tweet

conf = load_config(os.path.join(here, 'config.yaml'))

sqlite_dbs = [conf['databases']['dev']]

for fname in sqlite_dbs:
    try:
        print ("Removing {0}.".format(fname))
        os.remove(fname)
    except OSError:
        pass

for fname in sqlite_dbs:
    if os.path.isfile(fname):
        print ("Database {0} should not exist at this point!".format(fname))
    print("Creating empty SQLite file: {0}".format(fname))
    open(fname, 'a').close()

def class_from_name(module_name, class_name):
    c = getattr(module_name, class_name)
    return c

def get_classes (db):
    classes = []
    for str in conf['models'][db]:
        print ("\tCreating model for '{0}'".format(str))
        c = class_from_name(sys.modules[__name__], str)
        classes.append(c)
    return classes

start = time.clock()

mainDB.create_tables(get_classes('mainDB'))

url = "https://www.govtrack.us/api/v2/bill?congress=114"
response = urllib.urlopen(url)
data = json.loads(response.read())

for x in data['objects']:
    if x['is_alive']:
        Bill(ID                  = x['id'],
             title               = x['title'],
             display_num         = x['display_number'],
             bill_type           = x['bill_type'],
             bill_type_label     = x['bill_type_label'],
             congress            = x['congress'],
             current_status      = x['current_status'],
             current_status_date = x['current_status_date'],
             link_web            = x['link'],
             is_alive            = x['is_alive'],
             tweet_sum           = get_tweet(x['link']+"/summary")).save()
        #TODO 
        #PUT THE PARSING CODE HERE
        print("Added the Bill " +x['link'])
"""
for bill in Bill.select(): 
    summary = get_summaries(bill.link_web + "/summary") 
    if summary == "N/A": 
        pass 
    else: 
        for key in summary: 
            temp = callChain(summary[key]) 
            for ndx in range(len(temp['entities'])): 
                for lst_key in temp['entities'][ndx]: 
                    if lst_key == "salience": 
                        score = float(temp['entities'][ndx][lst_key])  
                    elif lst_key == "type": 
                        tyype = str(temp['entities'][ndx][lst_key])  
                    elif lst_key == "name": 
                        name = str(temp['entities'][ndx][lst_key]) 
                Salient(ID = bill.ID, 
                        summary = True, 
                        name = name, 
                        score = score, 
                        obj_type = tyype, 
                        section = key  
                        ).save()

for bill in Bill.select():    
    summary = get_summaries(bill.link_web + "/text")
    for key in summary:
        temp = callChain(summary[key])
        for ndx in range(len(temp['entities'])):
            for lst_key in temp['entities'][ndx]:
                if lst_key == "salience":
                    score = float(temp['entities'][ndx][lst_key])
                elif lst_key == "type":
                    tyype = str(temp['entities'][ndx][lst_key])
                elif lst_key == "name":
                    name = str(temp['entities'][ndx][lst_key])
            Salient(ID = bill.ID,
                    summary = False,
                    name = name,
                    score = score,
                    obj_type = tyype,
                    section = key
                    ).save() 
"""
print (time.clock() - start)    
