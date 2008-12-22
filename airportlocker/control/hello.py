import fab
import time

class HelloPage(fab.FabPage):
	title = "Hello, World!"

	template = fab.template('base.tmpl')
	body = fab.template('hello.tmpl')
	
	def control(self, page):
		page.message = "Hello, World!"

	def theTime(self):
		return time.asctime()
