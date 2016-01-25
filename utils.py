import re
import datetime
from tabulate import tabulate

def parseline(line):
    m = re.search(r'[ ]*(.*?)-(\d*?)\s*?\[(\d*)\]\s?(.*?)(\d{6}.\d{6}):\s?(.*)', line)

    if m is not None:
        l = re.split('\W', m.group(6))
        g = m.group
        g(1), int(g(2)), int(g(3)), g(4), datetime.datetime.fromtimestamp(float(g(5))), l[0], m.group(6)
        return g(1), int(g(2)), int(g(3)), g(4), datetime.datetime.fromtimestamp(float(g(5))), l[0], m.group(6)

    return None, None, None, None, None, None, None

def print_cpu_idle(d):
    i = 0
    cpus = d.getcpus()
    for cpu in cpus:
        if 'idle_time' in cpu:
            idle_time = (cpu['idle_time'].seconds * 1000000) + cpu['idle_time'].microseconds
            total_diff = d.end - d.start
            total = (total_diff.seconds * 1000000) + total_diff.microseconds
            percent = (idle_time * 100)/ float(total)
            print "{0}: idle {1}.{2} ({3:.3f}%) cs {4}".format(
                i, cpu['idle_time'].seconds,
                cpu['idle_time'].microseconds, percent, cpu['cs'])

        i += 1

    return

def print_syscall_info(d):
    table = []
    syscalls = d.getsyscalls()
    for syscall in syscalls:
        s = syscalls[syscall]
        total_time = (s['time'].second * 100000) + s['time'].microsecond
        if s['count'] > 0:
            average = float(total_time)/float(s['count'])
        else:
            average = 0
        table.append([syscall, s['count'], total_time, average])

    print tabulate(table)

    return

def print_syscall_by_process(d):
    process = d.getprocesses()
    for pid in process:
        p = process[pid].info
        print "{} ({})".format(process[pid].comm, pid)
        cpus = p['cpus']
        for i in range(len(cpus)):
            if not cpus[i]:
                continue
            print "CPU: ", i
            table = []
            for syscall in cpus[i]:
                if syscall in ['start']:
                    continue
                table.append([syscall,
                              "{}.{}".format(cpus[i][syscall]['total'].second,
                                             cpus[i][syscall]['total'].microsecond)])
            print tabulate(table)

    return
