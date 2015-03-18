#!/bin/bash

args_full=("$@")
url_sitemap=$1
baseurl_sitemap=$2
baseurl_one=$3
baseurl_two=$4
num_args_full=${#args_full[@]}
args_remaining=${args_full[@]:4:$num_args_full}

if [ "$url_sitemap" == "--help" ]; then
	echo 'Used to generate and run checks on two lists of corresponding URLs from a Google XML sitemap to be compared with each other.'
	echo 'Call with 4 arguments + all arguments to be passed to ./run_url_pairs_diff.sh:'
	echo '  1. url_sitemap       where to load the sitemap from'
	echo '  2. baseurl_sitemap   prefix to remove from all URLs read from sitemap'
	echo '  3. baseurl_one       prefix for "before" state in comparison'
	echo '  4. baseurl_sitemap   prefix for "after" state in comparison'
	echo ' ... remaining arguments are being passed on to ./run_url_pairs_diff.sh, try by adding --help at this point'
	echo '     You should at least set --upload_build_id at this point!'
	exit 0
fi

tmp_one=$(mktemp)
tmp_two=$(mktemp)

for url_sitemap in $(curl -L -s "$url_sitemap" | grep -o '<loc>\(.*\)' | sed -e "s|^\s*<loc>\(.*\)</loc>.*|\1|"); do
	url_template=$(sed -e "s|${baseurl_sitemap}|###BASEURL###|" <<< $url_sitemap)
	
	url_one=$(sed -e "s|###BASEURL###|${baseurl_one}|" <<< $url_template)
	url_two=$(sed -e "s|###BASEURL###|${baseurl_two}|" <<< $url_template)
	
	echo "${url_one}" >>"$tmp_one"
	echo "${url_two}" >>"$tmp_two"
done

./run_url_pairs_diff.sh $args_remaining "${tmp_one}" "${tmp_two}"

rm "$tmp_one"
rm "$tmp_two"
