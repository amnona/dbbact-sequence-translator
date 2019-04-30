# dbbact-sequence-translator
A REST-API server for connecting sequences from various 16S regions using a database of known sequences (i.e. SILVA/GreenGenes)

This server is used by the dbBact REST-API server for linking sequences spanning different 16S regions (V12/V34/V45/V67)

# Installation
## Activate the relevant dbBact conda environment (develop or main).
For information on creating such an environment see the dbBact-server installation instructions
```
source activate dbbact
```
## clone the repo:
```
git clone https://github.com/amnona/dbbact-sequence-translator.git
```

## install locally
```
cd dbbact-sequence-translator

pip install -e .
```

## setup the database and postgres user
```
psql -U postgres < database/setup.psql
```

## install the tables
for main:
```
pg_restore -U sequence_translator_dbbact -d sequence_translator_dbbact --no-owner database/format.psql
```

for develop:
```
pg_restore -U dev_sequence_translator_dbbact -d dev_sequence_translator_dbbact --no-owner database/format.psql
```

## download the SILVA (or greengenes) full fasta file (with all bacterial 16S sequences)

## create the different region fasta files:
### V4/5 (515f)
```
scripts/get_v4_region.py -i ~/whole_seqs/SILVA_132_SSURef_tax_silva.fasta -l 500 -f GTGCCAGC[AC]GCCGCGGTAA > ~/whole_seqs/silva_v4.fa
```
### V3/4 (341f)
```
scripts/get_v4_region.py -i ~/whole_seqs/SILVA_132_SSURef_tax_silva.fasta -l 500 -f CCTACGGG[ACGT][CGT]GC[AT][CG]CAG > ~/whole_seqs/silva_v3.fa
```

### V1/2 (27f)
```
scripts/get_v4_region.py -i ~/whole_seqs/SILVA_132_SSURef_tax_silva.fasta -l 500 -f AGAGTTTGATC[AC]TGGCTCAG > ~/whole_seqs/silva_v1.fa
```

## Install the region fasta files into the database
for main:
```
scripts/add_db_to_translator.py --server-type main -f ~/whole_seqs/silva_v1.fa -w silva -r 4 --no-index

scripts/add_db_to_translator.py --server-type main -f ~/whole_seqs/silva_v3.fa -w silva -r 3 --no-index

scripts/add_db_to_translator.py --server-type main -f ~/whole_seqs/silva_v4.fa -w silva -r 1
```

for develop:
```
scripts/add_db_to_translator.py --server-type develop -f ~/whole_seqs/silva_v1.fa -w silva -r 4  --no-index

scripts/add_db_to_translator.py --server-type develop -f ~/whole_seqs/silva_v3.fa -w silva -r 3  --no-index

scripts/add_db_to_translator.py --server-type develop -f ~/whole_seqs/silva_v4.fa -w silva -r 1
```

## run the sequence translator rest-api server to start listening on port 5021 (main) or 5022 (develop)
for main (run on port 5021):
```
export DBBACT_SEQUENCE_TRANSLATOR_SERVER_TYPE="main"
nohup gunicorn 'dbbact_sequence_translator.Server_Main:gunicorn(debug_level=3)' -b 0.0.0.0:5021 --workers 4 --name=main-sequence-translator-dbbact --timeout 300 --reload --capture-output --log-file log.txt
```

for develop (run on port 5022):
```
export DBBACT_SEQUENCE_TRANSLATOR_SERVER_TYPE="develop"
nohup gunicorn 'dbbact_sequence_translator.Server_Main:gunicorn(debug_level=3)' -b 0.0.0.0:5022 --workers 4 --name=dev-sequence-translator-dbbact --timeout 300 --reload --capture-output --log-file log.txt
```

## if this is the first time, need to export all dbbact-server sequences and add to fast conversion table
for main:
```
scripts/import_all_seqs.py
```

for develop:
```
scripts/import_all_seqs.py --seq-trans-addr http://0.0.0.0:5022
```