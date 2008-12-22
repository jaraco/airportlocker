# Makefile for fab
run: 
	PYTHONPATH=. python control/root.py

docs:
	fabDocBuilder.py doc/book/book.js doc/book/txt doc/book/html
	epydoc --html -o doc/api/lib lib
	epydoc --html -o doc/api/model model
	epydoc --html -o doc/api/control control
