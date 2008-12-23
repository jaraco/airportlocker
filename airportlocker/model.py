import uuid
from string import Template
from ottoman.client import OttomanServer, OttomanDocset

class LockerServer(OttomanServer):
	def docset(self, name):
		return Locker(self, name)

class LockerView(object):
	def __init__(self, field):
		self.field = field
		self.code = Template('''
def filter(i, val):
	if '$key' in i and i['$key'] == val:
		return i
''')

	def code(self):
		return self.code.safe_substitute({'key': self.field})


class Locker(OttomanDocset):

	@property
	def all(self):
		return [i[1] for i in self]

	def delete(self, id):
		oid = self[id]
		if oid:
			return OttomanDocset.delete(self, oid.keys()[0])
		return False

	def by_view(self, name, *args):
		vname = 'by_%s' % name
		try:
			return self.view(vname, *args)
		except:
			view = LockerView(name)
			self.define_view(vname, view.code())
		return self.view(vname, *args)

	def __getitem__(self, key):
		return self.view('by_id', key)

	def __init__(self, *args, **kw):
		OttomanDocset.__init__(self, *args, **kw)
		self.define_view('by_id',
'''
def filter(i, id):
	if i['_id'] == id:
		return i
''')



