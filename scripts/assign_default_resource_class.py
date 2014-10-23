from collections import Counter

import gridfs
import pymongo
import path

# con = pymongo.MongoClient('mgo11.ldc.yougov.local')
con = pymongo.MongoClient('vmgo10.paix.yougov.local')
fs = gridfs.GridFS(con.airportlocker, 'luggage')
files = con.airportlocker.luggage.files

res = files.update({'class': {'exists': False}},
                   {'$set': {'class': 'private'}},
                   multi=True)
print(res)

tally = Counter()
for file in files.find():
    filename = path.path(file['filename'].lstrip('/'))
    tally.update([file.get('class')])

for key in sorted(tally.keys()):
    print('{}: {}'.format(key, tally[key]))
