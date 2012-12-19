from optparse import OptionParser
import timeit

if __name__ == '__main__':
    usage = 'usage: %prog {airportlocker url}'
    parser = OptionParser()
    (options, args) = parser.parse_args()
    if args < 1:
        parser.error('I need the url!')
    stmt = "call(['python', 'exerciser.py', '%s'])" % args[0]
    timer = timeit.Timer(stmt, 'from subprocess import call')
    print timer.timeit(number=10)
