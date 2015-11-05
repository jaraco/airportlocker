import argparse
import timeit


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    stmt = "call(['python', 'exerciser.py', '%s'])" % args.url
    timer = timeit.Timer(stmt, 'from subprocess import call')
    print(timer.timeit(number=10))


if __name__ == '__main__':
    run()
