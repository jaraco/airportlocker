import gridfs
import pymongo
import path

con = pymongo.MongoClient('mgo11.ldc.yougov.local')
fs = gridfs.GridFS(con.airportlocker, 'luggage')
for file in fs.find():
	filename = path.path(file.filename.lstrip('/'))
	if filename.dirname():
		filename.dirname().makedirs_p()
	if filename.isfile():
		continue
	print("Writing", filename)
	with filename.open(mode='wb') as target:
		target.write(file.read())
