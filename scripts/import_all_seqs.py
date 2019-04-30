#!/usr/bin/env python

# Add the total counts of annotations and experiments for each sequence in dbbact

'''Add the total counts of annotations and experiments for each sequence in dbbact
'''

import sys
import requests

import argparse
import setproctitle

from dbbact_server import db_access
from dbbact_server.utils import debug, SetDebugLevel

__version__ = "0.9"


def add_seq_counts(con, cur, seq_trans_addr='http://127.0.0.1:5021'):
	debug(3, 'import_all_seqs started')
	debug(2, 'processing sequences')
	cur.execute('SELECT id, sequence FROM SequencesTable')
	seq_info = {}
	for cres in cur:
		cid = cres['id']
		cseq = cres['sequence']
		seq_info[cid] = cseq
	debug(2, 'found %d sequences' % len(seq_info))
	debug(2, 'adding to newsequencestable using rest-api')
	res = requests.post(seq_trans_addr + '/add_sequences_to_queue', json={'seq_info': seq_info})
	if res.status_code != 200:
		debug(5, 'failed! %s' % res.content)
	debug(3, 'done')


def main(argv):
	parser = argparse.ArgumentParser(description='import all sequences from dbbact into sequence_translator. version ' + __version__)
	parser.add_argument('--port', help='postgres port', default=5432, type=int)
	parser.add_argument('--host', help='postgres host', default=None)
	parser.add_argument('--database', help='postgres database', default='dbbact')
	parser.add_argument('--user', help='postgres user', default='dbbact')
	parser.add_argument('--password', help='postgres password', default='magNiv')
	parser.add_argument('--proc-title', help='name of the process (to view in ps aux)')
	parser.add_argument('--debug-level', help='debug level (1 for debug ... 9 for critical)', default=2, type=int)
	parser.add_argument('--seq-trans-addr', help='sequence translator rest-api address', default='http://127.0.0.1:5021')
	args = parser.parse_args(argv)

	SetDebugLevel(args.debug_level)
	# set the process name for ps aux
	if args.proc_title:
		setproctitle.setproctitle(args.proc_title)

	con, cur = db_access.connect_db(database=args.database, user=args.user, password=args.password, port=args.port, host=args.host)
	add_seq_counts(con, cur, seq_trans_addr=args.seq_trans_addr)


if __name__ == "__main__":
	main(sys.argv[1:])
