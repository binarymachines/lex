
init:
	cat required_dirs.txt | xargs mkdir -p 


clean:
	rm -f tempdata/*
	rm -f temp_scripts/*


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



pre-ingest:

	loopr -p -j --listfile tempdata/normalize_cmd_manifest.json \
	--cmd-string 'tail -n +1 tempdata/{outfile} | tuple2json --delimiter "|" --keys=application,is_renewal,type,date,status' \
	> tempdata/pre_ingest_cmds.txt

	tuplegen --delimiter '%' --listfiles=tempdata/output_files.txt,tempdata/pre_ingest_cmds.txt \
	| tuple2json --delimiter '%' --keys=outfile,cmd > tempdata/pre_ingest_cmd_manifest.json

	cp template_files/shell_script_core.sh.tpl temp_scripts/create_pre_ingest_files.sh

	loopr -p -j --listfile tempdata/pre_ingest_cmd_manifest.json \
	--cmd-string '{cmd} > data/{outfile}' >> temp_scripts/create_pre_ingest_files.sh

	chmod u+x temp_scripts/create_pre_ingest_files.sh
	temp_scripts/create_pre_ingest_files.sh


scratch:

	loopr -t --listfile tempdata/norm_files.txt --vartoken % \
	--cmd-string "tail -n -1 % | tuple2json --delimiter <delimiter> --datafile % --keys=app_code,type,date,status" \
	> tempdata/conversion_cmds.txt

