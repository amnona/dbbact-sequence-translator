#!/usr/bin/env python

import argparse
import sys

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


def add_whole_seq_names(con, cur, seqdb_id, whole_seq_fasta_name, db_type, add_only_species=True):
	'''
	'''
	debug(3, 'add_whole_seq_names started for database %d file %s' % (seqdb_id, whole_seq_fasta_name))

	db_type = db_type.lower()
	supported_dbs = ['silva']
	if db_type not in supported_dbs:
		raise ValueError('database type %s not supported. supported options are: %s' % (db_type, supported_dbs))

	# since we are inserting lots of values, lets drop the indices and add again at the end
	debug(1, 'dropping indices')
	cur.execute('DROP INDEX IF EXISTS wholeseqnamestable_wholeseqid_dbid_idx')
	cur.execute('DROP INDEX IF EXISTS wholeseqnamestable_wholeseqid_idx')
	cur.execute('DROP INDEX IF EXISTS wholeseqnamestable_species_idx')

	# iterate over the region specific whole sequence fasta file and add all sequences
	debug(1, 'processing fasta file %s' % whole_seq_fasta_name)
	seq_count = 0
	ok_seqs = 0
	no_species = 0
	for cseq, chead in iter_fasta_seqs(whole_seq_fasta_name):
		seq_count += 1
		# lets prepare the id string (sometimes has format 'ID.START.END TAXONOMY' we need to remove)
		cid = chead.split(' ')[0]
		split_cid = cid.split('.')
		if len(split_cid) > 2:
			cid = ".".join(split_cid[:-2])
		else:
			cid = ".".join(split_cid)
		cid = cid.lower()
		cseq = cseq.lower()

		if db_type == 'silva':
			taxstr = ' '.join(chead.split(' ')[1:])
			tt = taxstr.split(';')
			lastpos = len(tt) - 1
			found = False
			ctax = ''
			is_species = True
			while lastpos >= 0:
				bad = False
				ctax = tt[lastpos].lower()
				if len(ctax) == 0:
					bad = True
				if ctax.startswith('unidentified'):
					bad = True
				elif ctax.startswith('bacterium'):
					bad = True
				elif ctax.startswith('uncultured'):
					bad = True
				elif ctax.endswith('metagenome'):
					bad = True

				if bad:
					is_species = False
					lastpos -= 1
					continue
				found = True
				break
		else:
			raise ValueError("unsupported db_type %s" % db_type)
		if found:
			if is_species:
				cspecies = ctax
			else:
				no_species += 1
				cspecies = ''
				# we don't add non-species containing silva ids
				if add_only_species:
					continue
			cur.execute('INSERT INTO WholeSeqNamesTable (wholeseqid, dbid, name, fullname, species) VALUES (%s, %s, %s, %s, %s)', [cid, seqdb_id, ctax, chead.lower(), cspecies])
			ok_seqs += 1
		if seq_count % 10000 == 0:
			debug(1, 'processed %d' % seq_count)
	debug(2, 'scanned %s, found %d with no species, added %s sequences to SequenceIDs table' % (seq_count, no_species, ok_seqs))

	debug(2, 'adding indices')
	debug(2, 'wholeseqnamestable_wholeseqid_dbid_idx')
	cur.execute('CREATE INDEX "wholeseqnamestable_wholeseqid_dbid_idx" ON "public"."wholeseqnamestable"("wholeseqid","dbid")')
	debug(2, 'wholeseqnamestable_wholeseqid_idx')
	cur.execute('CREATE INDEX "wholeseqnamestable_wholeseqid_idx" ON "public"."wholeseqnamestable"("wholeseqid")')
	debug(2, 'wholeseqnamestable_species_idx')
	cur.execute('CREATE INDEX "wholeseqnamestable_species_idx" ON "public"."wholeseqnamestable"("species" text_pattern_ops)')

	debug(2, 'commiting')
	con.commit()
	debug(2, 'done')


def main(argv):
	parser = argparse.ArgumentParser(description='add_whole_seq_names version %s' % __version__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--port', help='postgres port', default=5432, type=int)
	parser.add_argument('--host', help='postgres host', default=None)
	parser.add_argument('--server-type', help='server type (develop/main/test). overridden by --database/user/password', default='main')
	parser.add_argument('--database', help='postgres database')
	parser.add_argument('--user', help='postgres user')
	parser.add_argument('--password', help='postgres password')

	parser.add_argument('--debug-level', help='debug level (1 for debug ... 9 for critical)', default=2, type=int)

	parser.add_argument('-f', '--wholeseq-file', help='name of the whole sequence fasta file (i.e. SILVA/etc.)', required=True)
	parser.add_argument('-w', '--wholeseqdb', help='id of the whole sequence database (from WholeSeqDatabaseTable, 1 is SILVA 13.2 etc)', type=int, required=True)
	parser.add_argument('-t', '--db-type', help='type of database added (for header taxonomy parsing) (currently supported: "SILVA")', default='SILVA')
	args = parser.parse_args(argv)

	SetDebugLevel(args.debug_level)

	# get the database connection
	con, cur = db_access.connect_translator_db(server_type=args.server_type, database=args.database, user=args.user, password=args.password, port=args.port, host=args.host)

	add_whole_seq_names(con, cur, seqdb_id=args.wholeseqdb, whole_seq_fasta_name=args.wholeseq_file, db_type=args.db_type)


if __name__ == "__main__":
	main(sys.argv[1:])
