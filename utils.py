import re
import datetime
from tabulate import tabulate
from collections import Mapping
from operator import add

def display_results(col_names, table):
    data = []
    data.append(col_names)
    data.extend([list(x) for x in table])
    print tabulate(data, headers='firstrow')

def parseline(line, return_type="list"):
    m = re.search(r'[ ]*(.*?)-(\d*?)\s*?\[(\d*)\]\s?(.*?)(\d{6}.\d{6}):\s?(.*)', line)

    if m is not None:
        l = re.split('\W', m.group(6))
        g = m.group
        if return_type == "dict":
            d = {}
            d['comm'] = g(1)
            d['pid'] = int(g(2))
            d['cpu'] = int(g(3))
            d['flags'] = g(4)
            d['timestamp'] = datetime.datetime.fromtimestamp(float(g(5)))
            d['name'] = l[0]
            d['buf'] = m.group(6)
            return d

        return g(1), int(g(2)), int(g(3)), g(4), datetime.datetime.fromtimestamp(float(g(5))), l[0], m.group(6)

    if return_type == "dict":
        return None

    return None, None, None, None, None, None, None

def parse_sched_details(buf):
    sched_details = {}
    c = buf.split(':', 1)[1].lstrip(' ').split(' ')
    for i in range(0, len(c)):
        if c[i] != '==>':
            l = c[i].split('=')
            if (len(l) > 1):
                sched_details[l[0]] = l[1]

    sched_details['next_pid'] = int(sched_details['next_pid'])
    sched_details['prev_pid'] = int(sched_details['prev_pid'])

    return sched_details


# from stackoverflow, Added the mapping part
def flattenMap(d, key_list=None, value_index=0, join=add, lift=lambda x:x, filter=None):
    _FLAG_FIRST = object()
    results = []
    def visit(subdict, results, partialKey):
        for k,v in subdict.items():
            if filter:
                if str(k) in filter:
                    continue
            newKey = lift(k) if partialKey==_FLAG_FIRST else join(partialKey,lift(k))
            if isinstance(v,Mapping):
                visit(v, results, newKey)
            else:
                results.append((newKey,v))
    visit(d, results, _FLAG_FIRST)
    if key_list is None:
        return results

    flat = []
    for k, v in dict(results).items():
        pairs = dict(zip(key_list, k))
        pairs[key_list[value_index - 1]] = v
        flat.append(pairs)

    return flat
