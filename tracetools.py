#!/usr/bin/python

# A attempt to integrate all tools which use ftrace to get various details.
#
# Santosh Sivaraj <santosiv@in.ibm.com>
#
# Based on scripts and tools by Paul Clarke, Greg Mewhinney and Shirin Khan

import sys

from tracedata import Data

from utils import print_syscall_by_process, print_syscall_info, print_cpu_idle


d = Data()

def main():
    if len(sys.argv) < 2:
        print "Insufficient Arguments"
        return

    tracefile = sys.argv[1]
    with open(tracefile, "r") as f:
        for l in f:
            d.process_trace(l)

    # print_syscall_by_process(d)
    # print_syscall_info(d)
    print_cpu_idle(d)

    return

if __name__ == '__main__':
	main()
