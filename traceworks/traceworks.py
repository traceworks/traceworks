#!/usr/bin/python
import json
import sys
import os
import re
import datetime
import sqlite3
import time
import argparse

from utils import parseline, display_results, flattenMap

bug_address="santosiv@in.ibm.com"

class TraceUtil:
    def __init__(self):
        cdir, filename = os.path.split(__file__)
        default_jsonconfig_path = os.path.join(cdir, "traceconfig.json")
        parser = argparse.ArgumentParser(description='''Work with traces.''',
                                         epilog='''See man page for more details.
                                         Report bugs to <{}>'''.format(bug_address),
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('tracefile', type=str, nargs='?', help='trace file')
        parser.add_argument('dbfile', type=str, nargs='?', default="tracedump.db",
                            help='sqlite3 database file')
        parser.add_argument('--type', '-t', type=str,
                            help='Top level type from the config file',
                            default='ftrace')
        parser.add_argument('--query', '-q', type=int, nargs='+',
                            help='the query number to run')
        parser.add_argument('--qargs', '-a', type=str, nargs='+',
                            help='arguments to the query if any')
        parser.add_argument('--list', '-l', action='store_true',
                            help='List all the available queries')
        parser.add_argument('--generate', '-g', action='store_true',
                            help='Store data in database from tracefile')
        parser.add_argument('--debug', '-d', action='store_true',
                            help='Print debug information')
        parser.add_argument('--config', '-c', type=str, nargs=1,
                            help='JSON config file', default=default_jsonconfig_path)
        parser.add_argument('--version', action='version', version='%(prog)s 1.0')



        if len(sys.argv) == 1:
            parser.print_usage()
            sys.exit(1)

        self.args = parser.parse_args()

        with open(self.args.config) as json_file:
            try:
                self.config = json.load(json_file)
            except ValueError:
                print "Invalid JSON file"
                exit(1)

        if 'traceworks' not in self.config:
            print "JSON file does not contain traceworks."
            exit(1)

        c = self.config['traceworks']
        if self.args.type not in c:
            print "Invalid config type. Available types in the config file are:"
            for i in c:
                print "   ", i

            exit(0)

        self.config = c[self.args.type][0]
        if 'queries' in self.config:
            self.queries = self.config['queries']
        else:
            self.queries = None

        if 'config' in self.config:
            self.config = self.config['config']
        else:
            self.config = None

        self.tracefile = self.args.tracefile
        self.data = {}

        return

    def debug(self, *message):
        if self.args.debug:
            print message
        return

    def initdb(self):
        self.conn = sqlite3.connect(self.args.dbfile)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        for i in range(len(self.config)):
            c = self.config[i]
            self.data[c['table_name']] = {}
            self.cursor.execute('DROP TABLE IF EXISTS {}'.format(c['table_name']))

            table_string = 'CREATE TABLE IF NOT EXISTS ' + c['table_name'] + '('
            # create table for each set of fields
            for j in range(len(c['fields'])):
                table_string += c['fields'][j] + ' ' + c['types'][j] + ','

            table_string = table_string.rstrip(',') + ')'
            self.cursor.execute(table_string)

        return

    def flatten_data(self, cfg):
        filter=cfg["filter"] if "filter" in cfg else None
        store_vars = []
        for a in ["exit_action", "entry_action"]:
            for f in cfg[a]:
                if f['store_name'] not in filter:
                    store_vars.append(f['store_name'])

        # flatten is required only if we have a hierarchy and only one end
        # value, if no hierarchy and multiple values in the dict, we don't
        # need a complicated flattening process
        #
        # case 1: (key1: {key2: {key3: {...: value}}})
        if len(store_vars) == 1:
            d = flattenMap(self.data[cfg['table_name']], key_list = cfg['fields'],
                           value_index = len(cfg['fields']),
                           lift=lambda a:(a,),
                           filter=filter)

            return d

        # case 2: (key1: {key2: {key2: value1, key3: value2}})
        if len(store_vars) > 1:
            d = flattenMap(self.data[cfg['table_name']], lift=lambda a: (a,))
            flat = []
            t = []
            i = 0
            for s in d:
                if set(s[0]).intersection(set(filter)):
                    continue
                t.append(s)
                i=i+1
                if i > len(store_vars) - 1:
                    i = 0
                    z = []
                    t1 = {}
                    for k, v in t:
                        for sk in k:
                            if sk not in z:
                                z.append(sk)
                        for sk in store_vars:
                            if sk in k:
                                t1[sk] = v
                    d1 = dict(zip(cfg['fields'], z))
                    d1.update(t1)
                    flat.append(d1)
                    t = []

            return flat

        return None

    def execute_action(self, parsed, d, actions):
        for action in actions:
            if action['store_name'] not in d:
                if action['type'] == "timestamp":
                    d[action['store_name']] = datetime.datetime.fromtimestamp(0)
                if action['type'] == "timedelta":
                    d[action['store_name']] = datetime.timedelta(0)
                else:
                    d[action['store_name']] = 0

            if action['operation'] == 'store':
                d[action['store_name']] = parsed[action['field']]
                d[action['store_name']]
            elif action['operation'] == 'difference':
                if action['field'] in d:
                    d[action['store_name']] += (parsed[action['field']] - d[action['field']])
            elif action['operation'] == "increment":
                d[action['store_name']] += 1


    def get_dict(self, hierarchy, parsed, data):
        d = data
        l = hierarchy.split("->")

        for i in range(len(l)):
            if parsed[l[i]] not in d:
                d[parsed[l[i]]] = {}
            d = d[parsed[l[i]]]

        if type(parsed['name']) is not str:
            print l, d, parsed
        return d

    def match_store(self, cfg, parsed):
        if cfg['name'] in parsed['name']:
            if "hierarchy" in cfg:
                d = self.get_dict(cfg["hierarchy"], parsed,
                                  self.data[cfg['table_name']])

                if 'entry_pattern' in cfg:
                    # check for a entry pattern, and see if this is entry or
                    # exit. One line can either be a entry or an exit, and any
                    # on of the actions will be executed, cannot be both.
                    if cfg['entry_pattern'] in parsed['buf']:
                        if 'entry_action' in cfg:
                            self.execute_action(parsed, d, cfg['entry_action'])
                    else:
                        if 'exit_action' in cfg:
                            self.execute_action(parsed, d, cfg['exit_action'])


                if 'exit_pattern' in cfg:
                    if cfg['exit_pattern'] in parsed['buf']:
                        if "exit_action" in cfg:
                            self.execute_action(parsed, d, cfg['exit_action'])
                    else:
                        if "entry_action" in cfg:
                            self.execute_action(parsed, d, cfg['entry_action'])

    def process_trace(self):
        if not self.args.tracefile:
            print "Cannot generate data without a tracefile"
            exit(1)

        with open(self.args.tracefile, "r") as f:
            for l in f:
                parsed = parseline(l, return_type="dict");
                if parsed is None:
                    continue

                for i in range(len(self.config)):
                    c = self.config[i]
                    self.match_store(c, parsed)

    def save_data(self, cfg, d):
        for t in d:
            insert_statement = "INSERT INTO {} VALUES (".format(cfg["table_name"])
            l = []
            for i in range(len(cfg['fields'])):
                insert_statement += '?,'
                val = t[cfg['fields'][i]]
                if cfg['types'][i] == "TIMESTAMP":
                    if type(val) is datetime.timedelta:
                        val = (val.seconds * 1000000) + val.microseconds
                    else:
                        val = time.mktime(val.timetuple())
                l.append(val)

            insert_statement = insert_statement.rstrip(',') + ')'
            self.debug(insert_statement, l)
            self.cursor.execute(insert_statement, l)

        return

    def list_queries(self):
        i = 1
        for q in self.queries:
            print "{}. {} ({})".format(i, q['name'], q['desc'])
            if 'args' in q and len(q['args']) > 0:
                print "    Requires the following {} argument(s)".format(len(q['args']))
                j = 1
                for a in q['args']:
                    print "      {}. {}".format(j, a)
            i += 1
        exit(0)

    def table_list_from_config(self):
        t = []
        for i in range(len(self.config)):
            t.append(self.config[i]['table_name'])

        return t

    def execute_query(self):
        for q in self.args.query:
            if q <= 0 or q > len(self.queries):
                print "Invalid query number {}".format(q)
                continue

            query = self.queries[q - 1]
            if 'query' not in query:
                print "Query not implemented"
                continue

            if "args" in query and len(query['args']) > 0:
                if not self.args.qargs:
                    print "query '{}' requires {} argument(s)".format(query["name"],
                                    len(query["args"]))
                    exit(1)
                qstr = query['query'].format(*self.args.qargs)
            else:
                qstr = query['query']

            tables = self.table_list_from_config();
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'");

            r = self.cursor.fetchall()
            db_tables = []
            for t in r:
                db_tables.append(t[0])

            if not set(db_tables).intersection(set(tables)):
                print 'Please generate the database from ftrace before querying'
                exit(1)

            self.cursor.execute(qstr)
            r = self.cursor.fetchall()
            col_names = list(map(lambda x: x[0], self.cursor.description))
            display_results(col_names, r)

        return

    def start(self):
        if self.args.list or self.args.query:
            if not self.queries or len(self.queries) == 0:
                print "No queries defined"
                exit(1)

        if self.args.list:
            self.list_queries()

        self.initdb()

        if self.args.generate:
            if not self.config or len(self.config) == 0:
                print "No config defined"
                exit(1)

            self.create_tables()
            self.collectall()

        if self.args.query:
            self.execute_query()

    def collectall(self):
        self.process_trace()
        for i in range(len(self.config)):
            c = self.config[i]
            self.debug(c['table_name'])
            d = self.flatten_data(c)
            if d:
                self.save_data(c, d)

    def finish(self):
        self.conn.commit()
        self.conn.close()
        return

if __name__ == '__main__':
    t = TraceUtil()
    t.start()
    t.finish()
