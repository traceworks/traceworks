from utils import parseline
import datetime
import multiprocessing

class Process:
    def __init__(self, comm, pid):
        self.comm = comm
        self.pid = pid

        self.info = {}
        self.idletime = 0

        return


class Data:
    def __init__(self):
        self.cpus = [{} for i in range(multiprocessing.cpu_count())]
        for cpu in self.cpus:
            cpu['idle_time'] = datetime.timedelta(0)
            cpu['cs'] = 0

        self.start = None
        self.end = None

        self.syscalls = {}
        self.process = {}

        return

    def add_data(self, cpu, pid, task):
        # self.cpus[cpu] = {}
        if pid not in self.process:
            self.process[pid] = Process(task, pid)
            self.process[pid].info['cpus'] = [{} for i in range(multiprocessing.cpu_count())]
            self.process[pid].info['start'] = None

        return

    def process_trace(self, line):
        task, pid, cpu, flags, timestamp, t, buf = parseline(line);

        if task is None:
            return

        self.add_data(cpu, pid, task)

        if not self.start:
            self.start = timestamp

        self.end = timestamp

        if "sys_" in t:
            self.process_syscall(cpu, pid, t, timestamp, buf)
            return

        if "sched_switch" in t:
            self.process_sched(cpu, pid, t, timestamp, buf)
            return

        return

    def getprocesses(self):
        return self.process

    def getsyscalls(self):
        return self.syscalls

    def getcpus(self):
        return self.cpus

    def process_syscall(self, cpu_id, pid, sc, timestamp, buf):
        p = self.process[pid].info
        cpu = p['cpus'][cpu_id]

        if sc not in self.syscalls:
            self.syscalls[sc] = {}
            self.syscalls[sc]['time'] = datetime.datetime.fromtimestamp(0)
            self.syscalls[sc]['count'] = 0

        syscall = self.syscalls[sc]

        if sc not in cpu:
            cpu[sc] = {}
            cpu[sc]['start'] = None
            cpu[sc]['total'] = datetime.datetime.fromtimestamp(0)

        if '->' in buf:
            # this is the syscall return
            if cpu[sc]['start']:
                cpu[sc]['total'] += timestamp - cpu[sc]['start']
                syscall['time'] += timestamp - cpu[sc]['start']
                syscall['count'] += 1
                cpu[sc]['start'] = None
        else:
            # This is the enter of the syscall
            cpu[sc]['start'] = timestamp

        return

    def process_sched(self, cpu_id, pid, sc, timestamp, buf):
        cpu = self.cpus[cpu_id]
        sched_details = {}
        c = buf.split(':', 1)[1].lstrip(' ').split(' ')
        for i in range(0, len(c)):
            if c[i] != '==>':
                l = c[i].split('=')
                if (len(l) > 1):
                    sched_details[l[0]] = l[1]

        sched_details['next_pid'] = int(sched_details['next_pid'])
        sched_details['prev_pid'] = int(sched_details['prev_pid'])

        if sched_details['next_pid'] == 0:
            # Here is a context switch, pid 0 is idle thread (swapper), this
            # CPU is going to idle now
            cpu['idle_in'] = timestamp

        if pid == 0:
            if 'idle_in' in cpu:
                cpu['idle_time'] += timestamp - cpu['idle_in']
                cpu['idle_in'] = None
                cpu['cs'] += 1
        return
