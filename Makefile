
init:
	cat required_dirs.txt | xargs mkdir -p 


clean:
	rm -f tempdata/*
	rm -f temp_scripts/*
	rm -f temp_sql/*


dblogin:
	psql -U lexdba --port=5432 --host=localhost -d lexdb


db-generate-dim-data:
	cat /dev/null > temp_sql/dimension_data.sql

	dgenr8 --plugin-module dim_day_generator --sql --schema public --dim-table dim_date_day --columns id value label \
	>> temp_sql/dimension_data.sql

	dgenr8 --plugin-module dim_month_generator --sql --schema public --dim-table dim_date_month --columns id value label \
	>> temp_sql/dimension_data.sql
	
	dgenr8 --plugin-module dim_year_generator --sql --schema public --dim-table dim_date_year --columns id value label \
	>> temp_sql/dimension_data.sql

	dgenr8 --plugin-module dim_permit_type_generator --sql --schema public --dim-table dim_permit_type --columns id value label \
	>> temp_sql/dimension_data.sql


db-create-tables:
	export PGPASSWORD=$$LEX_DB_PASSWORD && psql -w -d $$LEX_DB -h $$LEX_DB_HOST -p $$LEX_DB_PORT -U $$LEX_DB_USER -f sql/lex_db_extensions.sql
	export PGPASSWORD=$$LEX_DB_PASSWORD && psql -w -d $$LEX_DB -h $$LEX_DB_HOST -p $$LEX_DB_PORT -U $$LEX_DB_USER -f sql/lex.sql


db-populate-dimensions:
	export PGPASSWORD=$$LEX_DB_PASSWORD && psql -w -U $$LEX_DB_USER -d $$LEX_DB -h $$LEX_DB_HOST -p $$LEX_DB_PORT --file=temp_sql/dimension_data.sql


db-purge-dimensions:
	export PGPASSWORD=$$LEX_DB_PASSWORD && psql -w -U $$LEX_DB_USER -d $$LEX_DB -h $$LEX_DB_HOST -p $$LEX_DB_PORT \
	--file=sql/truncate_dimension_tables.sql


db-purge-facts:
	export PGPASSWORD=$$LEX_DB_PASSWORD && psql -w -U $$LEX_DB_USER -d $$LEX_DB -h $$LEX_DB_HOST -p $$LEX_DB_PORT \
	--file=sql/truncate_fact_tables.sql


db-purge-olap: db-purge-dimensions db-purge-facts



normalize:
	
	cat static_data/input_files.txt | sed "s/txt/jsonl/g" > tempdata/output_files.txt

	cat static_data/input_files.txt | sed "s/txt/norm.csv/g" > tempdata/norm_files.txt

	loopr -p -t --listfile static_data/input_files.txt --vartoken % \
	--cmd-string 'scripts/normalize static_data/%' > tempdata/norm_commands.txt

	tuplegen --delimiter "|" --listfiles=tempdata/norm_commands.txt,tempdata/norm_files.txt \
	| tuple2json --delimiter "|" --keys=command,outfile > tempdata/normalize_cmd_manifest.json

	cp template_files/shell_script_core.sh.tpl temp_scripts/normalize_input_files.sh

	loopr -p -j --listfile tempdata/normalize_cmd_manifest.json \
	--cmd-string '{command} > tempdata/{outfile}' >> temp_scripts/normalize_input_files.sh

	chmod u+x temp_scripts/normalize_input_files.sh
	temp_scripts/normalize_input_files.sh 



pre-ingest: clean normalize

	loopr -p -j --listfile tempdata/normalize_cmd_manifest.json \
	--cmd-string 'tail -n +2 tempdata/{outfile} | tuple2json --delimiter "|" --keys=application,is_renewal,type,date,status' \
	> tempdata/pre_ingest_cmds.txt

	tuplegen --delimiter '%' --listfiles=tempdata/output_files.txt,tempdata/pre_ingest_cmds.txt \
	| tuple2json --delimiter '%' --keys=outfile,cmd > tempdata/pre_ingest_cmd_manifest.json

	cp template_files/shell_script_core.sh.tpl temp_scripts/create_pre_ingest_files.sh

	loopr -p -j --listfile tempdata/pre_ingest_cmd_manifest.json \
	--cmd-string '{cmd} > data/{outfile}' >> temp_scripts/create_pre_ingest_files.sh

	chmod u+x temp_scripts/create_pre_ingest_files.sh
	temp_scripts/create_pre_ingest_files.sh


pipeline-lex:

	ls data/FOIL*.jsonl > tempdata/pre_ingest_files.txt

	cp template_files/shell_script_core.sh.tpl temp_scripts/ingest_records.sh

	loopr -p -t --listfile tempdata/pre_ingest_files.txt --vartoken '%' \
	--cmd-string 'cat % | ngst --config config/ingest_lexfiles.yaml --target db' \
	>> temp_scripts/ingest_records.sh

	chmod u+x temp_scripts/ingest_records.sh
	#temp_scripts/ingest_records.sh



scratch:

	loopr -t --listfile tempdata/norm_files.txt --vartoken % \
	--cmd-string "tail -n -1 % | tuple2json --delimiter <delimiter> --datafile % --keys=app_code,type,date,status" \
	> tempdata/conversion_cmds.txt

