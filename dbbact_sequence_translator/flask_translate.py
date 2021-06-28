import json
from flask import Blueprint, request, g
from . import db_translate
from .utils import debug, getdoc
from .autodoc import auto

Translate_Obj = Blueprint('Translate_Obj', __name__, template_folder='templates')


@Translate_Obj.route('/get_whole_seq_ids', methods=['POST', 'GET'])
@auto.doc()
def f_get_whole_seq_ids():
    """
    Title: Get IDs for a given sequence (from one of the supported regions)
    URL: /get_whole_seq_ids
    Method: GET/POST
    URL Params:
    Data Params: JSON
        {
            "sequence" : str
                the sequence to get the IDs for (acgt)
            "primer" : str
                name of the primer region (i.e. 'V4'). if region does not exist, will fail
        }
    Success Response:
        Code : 201
        Content :
        {
            "seq_ids" : list of str
                Whole sequence database ids matching the query sequence on the region (i.e. SILVA IDs etc.)
        }
    Details:
        Validation:
        Action:
        Add all sequences that don't already exist in SequencesTable
    """
    debug(3, 'f_get_whole_seq_ids', request)
    cfunc = f_get_whole_seq_ids
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequence = alldat.get('sequence')
    if sequence is None:
        return(getdoc(cfunc))
    primer = alldat.get('primer')
    # if primer is None:
    #     return(getdoc(cfunc))

    err, seqids = db_translate.get_whole_seq_ids(g.con, g.cur, sequence=sequence, primer=primer)
    if err:
        return(err, 400)
    debug(2, 'added/found %d sequences' % len(seqids))
    return json.dumps({"seq_ids": seqids})


@Translate_Obj.route('/get_dbbact_ids_from_wholeseq_ids', methods=['POST', 'GET'])
@auto.doc()
def f_get_dbbact_ids_from_wholeseq_ids():
    """
    Title: Get dbbact seqyuence IDs for a whole sequence database id (i.e. SILVA)
    URL: /get_dbbact_ids_from_wholeseq_ids
    Method: GET/POST
    URL Params:
    Data Params: JSON
        {
            "whole_seq_ids" : list of str
                list of the whole sequence ids to get the dbbact IDs for (i.e. for silva - jq772481)
            "dbname": str, optional
                name of the whole sequence database where the sequence ids are coming from (i.e. 'SILVA'/'GreenGenes')
        }
    Success Response:
        Code : 201
        Content :
        {
            "dbbact_ids" : list of list of int
                dbbact sequence ids for each corresponding whole_seq_id (note: can be more than 1 dbbact_id for each whole_seq_id since dbbact may contain several regions of same bacteria)
        }
    Details:
        Validation:
        Action:
        Add all sequences that don't already exist in SequencesTable
    """
    debug(3, 'f_get_dbbact_ids_from_wholeseq_ids', request)
    cfunc = f_get_dbbact_ids_from_wholeseq_ids
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    whole_seq_ids = alldat.get('whole_seq_ids')
    if whole_seq_ids is None:
        return(getdoc(cfunc))
    dbname = alldat.get('dbname')

    # err, dbbact_ids = db_translate.get_dbbact_ids_from_wholeseq_ids(g.con, g.cur, whole_seq_ids=whole_seq_ids, whole_seq_db_name=dbname, primer=primer)
    err, dbbact_ids = db_translate.get_dbbact_ids_from_wholeseq_ids(g.con, g.cur, whole_seq_ids=whole_seq_ids, whole_seq_db_name=dbname)
    if err:
        return(err, 400)
    return json.dumps({'dbbact_ids': dbbact_ids})


# @Translate_Obj.route('/test', methods=['POST', 'GET'])
# @auto.doc()
# def f_get_dbbact_ids_from_unknown_seq():
#     debug(3, 'f_get_dbbact_ids_from_unknown_seq', request)
#     alldat = request.get_json()
#     if alldat is None:
#         return('data not provided', 400)
#     seq = alldat.get('sequence')
#     if seq is None:
#         return('sequence value missing', 400)

#     err, whole_seq_ids = db_translate.get_whole_seq_ids(g.con, g.cur, seq)
#     if err:
#         return(err, 400)
#     if len(whole_seq_ids) == 0:
#         debug(2, 'sequence %s not found in whole_seq_db' % whole_seq_ids)
#     else:
#         debug(2, 'found %d whole_seq_db ids matchihng the sequence' % len(whole_seq_ids))
#     err, seq_ids = db_translate.get_dbbact_ids_from_wholeseq_ids(g.con, g.cur, whole_seq_ids=whole_seq_ids)
#     if err:
#         return(err, 400)
#     ret_seqs = set()
#     for k, v in seq_ids.items():
#         ret_seqs = ret_seqs.union(set(v))
#     debug(2, 'found %d dbbact ids' % len(ret_seqs))
#     return json.dumps({'dbbact_ids': list(ret_seqs)})
#     # return json.dumps({'dbbact_ids': list(ret_seqs), 'silva_ids': seq_ids})


@Translate_Obj.route('/add_sequences_to_queue', methods=['POST', 'GET'])
def f_add_sequences_to_queue():
    '''add a sequence to the processing queue table

    seq_info:
        dict of {seq_id(int): seq(str)}
            key is the dbbact sequence id, value is the sequence
    '''
    debug(3, 'f_add_sequences_to_queue', request=request)
    # only allow from local server
    if request.remote_addr != '127.0.0.1':
        debug(3, 'got remote request for add_sequences_to_queue. ignoring', request=request)
        return ('access forbidden', 403)
    alldat = request.get_json()
    seq_info = alldat.get('seq_info')
    err = db_translate.add_sequences_to_queue(g.con, g.cur, seq_info=seq_info)
    if err:
        return (err, 400)
    return 'ok'


@Translate_Obj.route('/get_ids_for_seqs', methods=['POST', 'GET'])
@auto.doc()
def f_get_dbbact_ids_from_unknown_seq_fast():
    '''
    Title: Get dbBact IDs for a given sequence (from one of the supported regions)
    URL: /get_ids_for_seqs
    Method: GET/POST
    URL Params:
    Data Params: JSON
        {
            "sequences" : str
                the sequences to get the IDs for (acgt)
        }
    Success Response:
        Code : 201
        Content :
        {
            "dbbact_ids" : list of list of int
                each item is a list of dbBact ids that have the original sequence in one of the supported regions in a SILVA sequence
        }
    Details:
        Validation:
        Action:
        Get dbbact sequenceIDs for all SILVA sequences matching the sequences on one of the supported regions (V1, V3, V4)
    '''
    debug(3, 'f_get_dbbact_ids_from_unknown_seq_fast', request)
    alldat = request.get_json()
    if alldat is None:
        return('data not provided', 400)
    seq = alldat.get('sequences')
    if seq is None:
        return('sequences value missing', 400)

    err, dbbact_ids = db_translate.get_dbbact_ids_from_wholeseq_ids_fast(g.con, g.cur, seq)
    if err:
        return(err, 400)
    if len(dbbact_ids) == 0:
        debug(2, 'no matching dbbact ids for original sequence %s found' % seq)
    else:
        debug(2, 'found %d dbbacct ids matchihng the sequence' % len(dbbact_ids))
    return json.dumps({'dbbact_ids': dbbact_ids})
    # return json.dumps({'dbbact_ids': list(ret_seqs), 'silva_ids': seq_ids})


@Translate_Obj.route('/get_whole_seq_taxonomy', methods=['POST', 'GET'])
@auto.doc()
def f_get_whole_seq_taxonomy():
    """
    Title: Get SILVA taxonomy strings for a given sequence (from one of the supported regions)
    URL: /get_whole_seq_taxonomy
    Method: GET/POST
    URL Params:
    Data Params: JSON
        {
            sequence : str
                the sequence (ACGT) to get the wholeseqdb taxonomies for
            "whole_seq_db_id": int or None, optional
                the id (from wholeseqdatabasetable) of the whole sequence database to use (1 for silva 13.2, etc.)
                0 or None to use taxonomies from all databases
        }
    Success Response:
        Code : 201
        Content :
        {
            "seq_ids" : list of str
                Whole sequence database ids matching the query sequence on the region (i.e. SILVA IDs such as jq782411 etc.)
            "names": list of str
                The highest resolution names matching the query sequence on the region (i.e. 'lactobacillus rhamnosus')
            "full_names": list of str
                The full fasta headers matching the query sequence on the region (i.e. '>JQ782411.1.1419 Bacteria;Firmicutes;Bacilli;Lactobacillales;Lactobacillaceae;Lactobacillus;Lactobacillus rhamnosus')
            "species": list of str
                the species name matching the query sequence. if no species name is available, empty string ''
            "ids": list of str
                the whole sequence database id of each match (i.e. 'JQ782411')
        }
    Details:
        Validation:
        Action:
        Add all sequences that don't already exist in SequencesTable
    """
    debug(3, 'f_get_whole_seq_taxonomy', request)
    cfunc = f_get_whole_seq_taxonomy
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequence = alldat.get('sequence')
    if sequence is None:
        return(getdoc(cfunc))
    whole_seq_db_id = alldat.get('whole_seq_db_id')
    if whole_seq_db_id is None:
        whole_seq_db_id = 0

    err, seqids = db_translate.get_whole_seq_ids(g.con, g.cur, sequence=sequence)
    if err:
        return(err, 400)

    debug(2, 'found %d wholeseq matching sequences' % len(seqids))
    err, names, fullnames, species, ids = db_translate.get_whole_seq_names(g.con, g.cur, whole_seq_ids=seqids, dbid=whole_seq_db_id)
    return json.dumps({"seq_ids": seqids, "names": names, "fullnames": fullnames, 'species': species, 'ids': ids})


@Translate_Obj.route('/get_species_seqs', methods=['POST', 'GET'])
@auto.doc()
def f_get_species_seqs_f():
    """
    Title: Get dbBact sequence ids matching a given SILVA specien name
    URL: /get_species_seqs
    Method: GET/POST
    URL Params:
    Data Params: JSON
        {
            "species" : str
                the species to search for (i.e. "akkermansia muciniphila")
            "whole_seq_db_id": int or None, optional
                the id (from wholeseqdatabasetable) of the whole sequence database to use (1 for silva 13.2, etc.)
                0 or None to use taxonomies from all databases
        }
    Success Response:
        Code : 201
        Content :
        {
            "ids" : list of int
                dbBact sequence ids matching any of the SILVA sequences that have this species name
        }
    Details:
        Validation:
        Action:
        Add all sequences that don't already exist in SequencesTable
    """
    debug(3, 'f_get_species_seqs_f', request)
    cfunc = f_get_species_seqs_f
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    species = alldat.get('species')
    if species is None:
        return(getdoc(cfunc))
    whole_seq_db_id = alldat.get('whole_seq_db_id')
    if whole_seq_db_id is None:
        whole_seq_db_id = 0
    err, ids = db_translate.get_species_seqs(g.con, g.cur, species, whole_seq_db_id)
    return json.dumps({"ids": ids})
