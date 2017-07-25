# Traceworks

Parse and analyse data from Linux ftrace.

This tool helps to parse the traces from the Linux kernel, and help to analyse
using custom queries.

## Why `traceworks`?

* trace is a good method of identifying performance problems
* Manually analysing and walking through the huge traces is a pain
* Simple parsing tool can help simplying the process by getting specific
  information in matter of seconds
* Specific tracepoints can be turned on or off, which require lot of parsing
  tools for a specific job
* Combining and getting them under a common umbrella for wider reach and
  reusability is needed.
* ftrace is a key tracing infrastructure on Linux.

### Information that can be collected

A partial list

- Process runtimes
- System call time by CPU or Process
- Process CPU migration history
- Locks
- Interrupts
- CPU idle time

## How it works?

Uses a python regular expression to parse the ftrace file and extract useful
information and stores in a `sqlite` database. What data to extract and how to
save is described in a config file. The config file is in JSON format.

A JSON based config file, which contains what to ’grep’ for and what to data to
collect and store Based on the config file, tables are created in a sqlite
database, which is convinient for repeated queries, otherwise which takes
minutes to parse a normal trace file.

The queries in the config file are basic SQL statements.

![Traceworks Stack](/doc/imgs/traceworks-arch.png)

## Installation

```sh
$ sudo python setup.py install
```

## Usage

```sh
$ traceworks [OPTION]... [dbfile] [tracefile]

$ traceworks [-h] [--query QUERY [QUERY ...]] [--qargs QARGS [QARGS ...]] [--list] [--generate] [--debug] [--config CONFIG] [--version] [tracefile] [dbfile]
```

### Arguments

- tracefile - ftrace file (default: None)
- sqlite3 database file (default: tracedump.db)

### Optional arguments

**−h**, **−−help**

show this help message and exit

**−−query** QUERY \[QUERY ...\], **−q** QUERY \[QUERY ...\]

the query number to run (default: None)

**−−qargs** QARGS \[QARGS ...\], **−a** QARGS \[QARGS ...\]

arguments to the query if any (default: None)

**−−list**, **−l**

List all the available queries (default: False)

**−−generate**, **−g**

Store data in database from tracefile (default: False)

**−−debug**, **−d**

Print debug information (default: False)

**−−config** CONFIG, **−c** CONFIG

JSON config file (default: traceconfig.json)

**−−version**

show program’s version number and exit

### Generate database tables from trace

```sh
$ traceworks -g tracefile
```

### List all queries

```sh
$ traceworks -l
1. process names (Map process names and PIDs)
2. cpuidle (List idle times of each CPU)
3. syscall duration for a pid (List time taken by each syscall for a process)
    Requires the following 1 argument(s)
      1. pid
4. syscall duration (List time taken by each syscall)
5. syscall duration by cpu (List the time taken by each system call on each CPU)
6. Top n syscalls (List the top n syscalls that consume cpu time)
    Requires the following 1 argument(s)
      1. number
```


### Querying

Query contect switches
```sh
$ traceworks -q 2
  cpu    idle_time    context_switches
-----  -----------  ------------------
    0      3060257                 587
    1      3200971                 354
    2      3763700                1215
    3      4295133                 938
```

## Contributing

Anybody is welcome to contribute to the project. Some general rules to
contribution are:

- Follow the standard
  indentation
  [practices](https://www.python.org/dev/peps/pep-0008/#code-lay-out)
- Use spaces than tabs in the code.
- Test changes using both python version 2 and 3.
- Do not do too much in one commit, split into small, logical and self-contained
  patches.
- Follow the general git
  commit [standards](https://chris.beams.io/posts/git-commit/)
