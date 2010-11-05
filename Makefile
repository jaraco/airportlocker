# Makefile for fab
run: 
	PYTHONPATH=. monster_run devel.yaml airportlocker.main
docs:
	fabDocBuilder.py doc/book/book.js doc/book/txt doc/book/html
	epydoc --html -o doc/api/lib lib
	epydoc --html -o doc/api/model model
	epydoc --html -o doc/api/control control

start-backend:
	faststored 10110 file_metadata &

tt:
	ttserver -port 10120 -ext 'storage/tt_lua/faststore.lua' filestore_metadata.tch#bcnum=500000

tt-release:
	ttserver -port 10120 -ext '/home/eric.larson/release/gryphon/storage/tt_lua/faststore.lua' filestore_metadata.tch#bcnum=500000