#!/usr/bin/env python

import argparse
import sys

import setproctitle

from dbbact_sequence_translator.utils import debug, SetDebugLevel
from dbbact_sequence_translator import db_access


__version__ = 1.1


def iter_fasta_seqs(filename):
	"""
	iterate a fasta file and return header,sequence
	input:
	filename - the fasta file name

	output:
	seq - the sequence
	header - the header
	"""

	fl = open(filename, "rU")
	cseq = ''
	chead = ''
	for cline in fl:
		if cline[0] == '>':
			if chead:
				yield(cseq.lower(), chead)
			cseq = ''
			chead = cline[1:].rstrip()
		else:
			cline = cline.strip().lower()
			cline = cline.replace('u', 't')
			cseq += cline.strip()
	if cseq:
		yield(cseq, chead)
	fl.close()


def add_db_to_translator(con, cur, seqdbname, whole_seq_fasta_name, region=0, no_index=False):
	'''
	**kwargs:
		server_type=None, database=None, user=None, password=None, port=None, host=None
	'''
	debug(3, 'add_db_to_translator started for database %s' % seqdbname)

	# since we are inserting lots of values, lets drop the indices and add again at the end
	debug(1, 'dropping indices')
	cur.execute('DROP INDEX IF EXISTS sequenceidstable_wholeseqid_idx')
	cur.execute('DROP INDEX IF EXISTS sequenceidstable_sequence_idx')

	# iterate over the region specific whole sequence fasta file and add all sequences
	debug(1, 'processing fasta file %s' % whole_seq_fasta_name)
	seq_count = 0
	for cseq, chead in iter_fasta_seqs(whole_seq_fasta_name):
		# lets prepare the id string (sometimes has format 'ID.START.END TAXONOMY' we need to remove)
		cid = chead.split(' ')[0]
		split_cid = cid.split('.')
		if len(split_cid) > 2:
			cid = ".".join(split_cid[:-2])
		else:
			cid = ".".join(split_cid)
		cid = cid.lower()
		cseq = cseq.lower()
		cur.execute('INSERT INTO SequenceIDsTable (sequence, wholeseqid, wholeseqdb, region) VALUES (%s, %s, %s, %s)', [cseq, cid, seqdbname, region])
		seq_count += 1
		if seq_count % 10000 == 0:
			debug(1, 'processed %d' % seq_count)
	debug(2, 'added %s sequences to SequenceIDs table' % seq_count)
	if no_index:
		debug(3, 'skipping add index. NOTE: must add later for optimal performance')
	else:
		debug(2, 'adding indices')
		# we use the text_pattern_ops on the index, so querying left substring is same speed as exact query
		# this way we can add long sequences to the table and query the subsequence
		cur.execute('CREATE INDEX sequenceidstable_sequence_idx ON SequenceIDsTable (sequence text_pattern_ops)')
		cur.execute('CREATE INDEX sequenceidstable_wholeseqid_idx ON SequenceIDsTable (sequence)')
	debug(2, 'commiting')
	con.commit()
	debug(2, 'done')


def main(argv):
	parser = argparse.ArgumentParser(description='add_db_to_translator version %s' % __version__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--port', help='postgres port', default=5432, type=int)
	parser.add_argument('--host', help='postgres host', default=None)
	parser.add_argument('--server-type', help='server type (develop/main/test). overridden by --database/user/password')
	parser.add_argument('--database', help='postgres database')
	parser.add_argument('--user', help='postgres user')
	parser.add_argument('--password', help='postgres password')
	parser.add_argument('--proc-title', help='name of the process (to view in ps aux)')
	parser.add_argument('--debug-level', help='debug level (1 for debug ... 9 for critical)', default=2, type=int)
	parser.add_argument('--no-index', help='no index creation after adding sequences (if adding multiple regions)', action='store_true')

	parser.add_argument('-f', '--wholeseq-file', help='name of the whole sequence region fasta file (can be very long length for each sequence since we use left substring for match)', required=True)
	parser.add_argument('-w', '--wholeseqdb', help='name of the whole sequence database (i.e. SILVA/GREENGENES)', default='SILVA')
	parser.add_argument('-r', '--region', help='primer region id (1=v4, 3=v3,... 0 for unspecified)', type=int, default=0)
	args = parser.parse_args(argv)

	SetDebugLevel(args.debug_level)
	# set the process name for ps aux
	if args.proc_title:
		setproctitle.setproctitle(args.proc_title)

	# get the database connection
	con, cur = db_access.connect_translator_db(server_type=args.server_type, database=args.database, user=args.user, password=args.password, port=args.port, host=args.host)

	add_db_to_translator(con, cur, seqdbname=args.wholeseqdb, whole_seq_fasta_name=args.wholeseq_file, region=args.region, no_index=args.no_index)


if __name__ == "__main__":
	main(sys.argv[1:])
