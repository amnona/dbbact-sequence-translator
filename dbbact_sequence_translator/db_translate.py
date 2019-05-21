import psycopg2

from .utils import debug


def get_whole_seq_ids(con, cur, sequence, primer=None, exact=False):
	'''get ids for all the sequences matching the given seqeunce

	Parameters
	----------
	con, cur
	sequence: str
		the sequence to look for (acgt). needs to be from the beginning of a region added to the database
	primer: str, optional
	exact: bool, optional
		False (default) to find sequences beginning with sequence
		True to look for exact match only

	Returns
	-------
	list of str
		the ids matching (i.e. SILVA ids, etc.)
	'''
	if len(sequence) < 100:
		return 'sequence too short. must be at least 100bp: %s' % sequence, []
	sequence = sequence.lower()
	if len(sequence) < 100:
		return 'sequence length < 100bp for sequence %s' % sequence, []
	if primer is not None:
		primer = primer.lower()
	if not exact:
		debug(1, 'looking for non exact matches for sequence %s' % sequence)
		cur.execute('SELECT * FROM SequenceIDsTable WHERE sequence LIKE %s', [sequence + '%%'])
	else:
		debug(1, 'looking for exact matches for sequence %s' % sequence)
		cur.execute('SELECT * FROM SequenceIDsTable WHERE sequence=%s', [sequence])

	if cur.rowcount == 0:
		debug(1, 'no matches found')
		return '', []

	debug(1, 'found %d matches' % cur.rowcount)
	seqids = []
	res = cur.fetchall()
	for cres in res:
		if primer is not None:
			if cres['primer'] != primer:
				continue
		seqids.append(cres['wholeseqid'])
	debug(2, 'found %d matches with correct region' % len(seqids))
	return '', seqids


def get_seqs_from_db_id(con, cur, db_name, db_seq_id):
	'''Get all sequences that match the db_seq_id supplied for silva/greengenes

	Parameters
	----------
	con, cur
	db_name: str
		name of the database from which the id originates. can be "silva" or "gg"
	db_seq_id: str
		the sequence identifier in the database (i.e. 'FJ978486' for silva or '1111883' for greengenes)

	Returns
	-------
	error: str or '' if ok
	list of int
		the dbbact ids for all the dbbact sequences matching the db_seq_id
	list of str
		the actual sequences for the dbbact sequences matching the db_seq_id (same order)
	'''
	database_ids = {'silva': 1, 'gg': 2}
	if db_name in database_ids:
		db_id = database_ids[db_name]
	else:
		err = 'database id %s not found. options are: %s' % database_ids.keys()
		debug(9, err)
		return err, [], []
	db_seq_id = db_seq_id.lower()
	cur.execute("SELECT id,sequence FROM SequencesTable where id in (select distinct dbbactid from WholeSeqIDsTable where WholeSeqID=%s AND dbid=%s)", [db_seq_id, db_id])
	seq_ids = []
	sequences = []
	res = cur.fetchall()
	for cres in res:
		seq_ids.append(cres[0])
		sequences.append(cres[1])
	debug(1, 'found %d dbbact sequences for seqid %s' % (len(seq_ids), db_seq_id))
	return '', seq_ids, sequences


def SequencesWholeToFile(con, cur, fileName, dbid):
	'''
	Save list of sequences to file, this will be used later 'whole' ids script

	Parameters
	----------
	con,cur
	fileName - output file name
	dbid - type of db (e.g. silva)

	Returns
	-------
	error message
	'''
	debug(1, 'SequencesWholeToFile')

	try:
		# cur.execute("SELECT id,sequence,ggid FROM sequencestable")
		cur.execute("SELECT id,sequence,ggid FROM sequencestable where id not in (select distinct dbbactid from wholeseqidstable where dbid=%s)" % dbid)

		seq_count = 0
		with open(fileName, 'w') as fl:
			for cres in cur:
				fl.write('>%s\n%s\n' % (cres[0], cres[1]))
				seq_count += 1
	except psycopg2.DatabaseError as e:
		debug(7, 'database error %s' % e)
		return "database error %s" % e
	return ''


def add_whole_seq_id(con, cur, dbidVal, dbbactidVal, wholeseqidVal, commit=True):
	'''
	Add record to WholeSeqIDsTable table

	Parameters
	----------
	con,cur
	dbidVal: int
		whole seq db id (from get_whole_seq_db_id_from_name()) (e.g. 1 for silva, 2 for greengenes etc)
	dbbactidVal: int
		sequnence id in dbbact
	wholeseqidVal: str
		the id in different db (e.g. silva, gg)
	commit: bool, optional
		true to commit, false to insert without commit

	Returns
	-------
	str: error message or empty string ('') if ok
	'''
	debug(1, 'add_whole_seq_id')
	try:
		# check if we already have this entry
		err, existFlag = test_whole_seq_id_exists(con, cur, dbidVal, dbbactidVal, wholeseqidVal)
		if not existFlag:
			cur.execute('INSERT INTO wholeseqidstable (dbid, dbbactid, wholeseqid) VALUES (%s, %s, %s)', [dbidVal, dbbactidVal, wholeseqidVal])
			if commit:
				con.commit()
		return
	except psycopg2.DatabaseError as e:
		debug(7, 'database error %s' % e)
		return "database error %s" % e


def test_whole_seq_id_exists(con, cur, dbidVal, dbbactidVal, wholeseqidVal=None):
	'''
	Check if record already exists in wholeseqidstable table

	Parameters
	----------
	con,cur
	dbidVal - db type (e.g. silva, gg)
	dbbactidVal - sequnence id in dbbact
	wholeseqidVal: str or None, optional
		if not None, search for a match also for the wholeseqidVal id in different db (e.g. silva, gg)
		if None, retrive all the ids which have at list one record

	Returns
	-------
	err: empty ('') if query went ok, otherwise contains the database error
	exists: True if record exists in wholeSeqIDsTalbe, False otherwise
	'''
	debug(1, 'test_whole_seq_id_exists for database %s dbbact_id %s wholeseqid %s' % (dbidVal, dbbactidVal, wholeseqidVal))

	try:
		if wholeseqidVal is not None:
			cur.execute("SELECT * FROM WholeSeqIDsTable where dbID = %s and dbbactID = %s and WholeSeqID = %s", [dbidVal, dbbactidVal, wholeseqidVal])
		else:
			cur.execute("SELECT * FROM WholeSeqIDsTable where dbID = %s and dbbactID = %s", [dbidVal, dbbactidVal])
		if cur.rowcount > 0:
			return "", True
		else:
			return "", False

	except psycopg2.DatabaseError as e:
		debug(7, 'database error %s' % e)
		return "database error %s" % e, False


def get_dbbact_ids_from_wholeseq_ids(con, cur, whole_seq_ids, whole_seq_db_name=None, whole_seq_db_version=None):
	'''Get all sequences that match the db_seq_id supplied for silva/greengenes

	Parameters
	----------
	con, cur
	whole_seq_db_name: str
		name of the database from which the id originates. can be "silva" or "gg"
	whole_seq_db_version: str or None, optional
		version of the whole seq database, or None to get latest
	whole_seq_ids: list of str
		the sequence identifiers in the whole seq database (i.e. 'FJ978486' for silva or '1111883' for greengenes)

	Returns
	-------
	error: str or '' if ok
	ids : list of list on int
		list of dbbact ids (value) for all the dbbact sequences matching each whole_seq_id (ordered same as whole_seq_ids)
	'''
	debug(1, 'get_dbbact_ids_from_wholeseq_ids for db %s version %s' % (whole_seq_db_name, whole_seq_db_version))
	if whole_seq_db_name is not None:
		whole_seq_db_name = whole_seq_db_name.lower()
		err, whole_seq_db_id = get_whole_seq_db_id_from_name(con, cur, whole_seq_db_name, whole_seq_db_version)
		if err:
			debug(6, 'could not get dbbact seq ids. err=%s' % err)
			return err, []
	else:
		whole_seq_db_id = None
	try:
		dbids = []
		for cseq in whole_seq_ids:
			cids = set()
			cseq = cseq.lower()
			if whole_seq_db_id is None:
				cur.execute('SELECT dbbactID FROM WholeSeqIDsTable WHERE WholeSeqID=%s', [cseq])
			else:
				cur.execute('SELECT dbbactID FROM WholeSeqIDsTable WHERE WholeSeqID=%s AND dbid=%s', [cseq, whole_seq_db_id])
			res = cur.fetchall()
			for cres in res:
				cids.add(cres['dbbactid'])
			dbids.append(list(cids))
		return '', dbids
	except Exception as e:
		msg = 'error encountered when getting dbbact ids from whole seq ids: %s' % e
		debug(3, msg)
		return msg, None


def get_whole_seq_db_id_from_name(con, cur, whole_seq_db_name, whole_seq_db_version=None):
	'''Get the whole seq database id from the whole seq database name ((i.e. 1 for SILVA, 2 for GreenGenes).

	Parameters
	----------
	whole_seq_db_name: str
		name of the whole seq database (i.e. SILVA, GreenGenes, etc.)
	whole_seq_db_version: str or None, optional
		if None, get the latest version of the database. if not none, use the specific version (i.e. 13.5 etc.)

	Returns
	-------
	int: the whole seq database id (used in other tables)
	'''
	whole_seq_db_name = whole_seq_db_name.lower()
	debug(1, 'get_wholeseq_db_id_from_name for db %s version %s' % (whole_seq_db_name, whole_seq_db_version))
	try:
		if whole_seq_db_version is None:
			cur.execute('SELECT dbid, version FROM WholeSeqDatabaseTable WHERE dbName=%s ORDER BY version DESC', [whole_seq_db_name])
		else:
			cur.execute('SELECT dbId FROM WholeSeqDatabaseTable WHERE dbName=%s AND version=%s', [whole_seq_db_name, whole_seq_db_version])
		if cur.rowcount == 0:
			debug(1, 'no match to database found')
			return('No match found', None)
		res = cur.fetchone()
		dbid = res['dbid']
		debug(1, 'database id is: %d' % dbid)
		return '', dbid
	except Exception as e:
		msg = 'error encountered when getting whole sequence database id: %s' % e
		debug(3, msg)
		return msg, None


def add_sequences_to_queue(con, cur, seq_info, commit=True):
	'''Add sequences to the waiting for processing table.
	These sequences will be added daily to the wholeseqids table

	Parameters
	----------
	con, cur
	seq_info: dict of {dbbactid(int): sequences(str)}
	commit: bool, optional
		true to commit, false to insert without commit

	Returns
	-------
	err: '' if ok or error string if error encountered
	'''
	debug(3, 'add_sequences_to_queue for %d sequences' % len(seq_info))
	try:
		for cid, cseq in seq_info.items():
			cseq = cseq.lower()
			cur.execute('INSERT INTO NewSequencesTable (dbbactID, sequence) VALUES (%s, %s)', [cid, cseq])
		debug(3, 'added %d sequences' % len(seq_info))
		if commit:
			con.commit()
		return ''
	except Exception as e:
		debug(6, 'error enountered when adding sequences to queue: %s' % e)
		return e


def get_dbbact_ids_from_wholeseq_ids_fast(con, cur, seqs):
	'''Get dbbact ids for sequences on all regions by using wholeseq databases (SILVA.GreenGenes/etc).
	This is a fast function using the SequenceToSequence Table which is precomputed.

	Parameters
	----------
	con, cur
	seqs: list of str
		The sequences to find

	Returns
	-------
	list of list of int:
		the matching dbbact ids for each input sequence
	'''
	all_seq_ids = []
	for cseq in seqs:
		cseq = cseq.lower()
		cur.execute('SELECT dbbactIDs FROM SequenceToSequenceTable WHERE sequence LIKE %s LIMIT 1', [cseq + '%%'])
		if cur.rowcount == 0:
			ids = []
		else:
			res = cur.fetchone()
			ids_str = res['dbbactids']
			ids = [int(x) for x in ids_str.split(',')]
		all_seq_ids.append(ids)
	return '', all_seq_ids
