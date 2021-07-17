#!/bin/bash
set -o errexit
set -o pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

args=("$@")

# TOX_ENV_RE is set on CI to filter the default environment list
if [[ $TOX_ENV_RE != "" ]] ; then
	if [[ "${#args[@]}" -gt 0 ]] ; then
		echo "TOX_ENV_RE and command line arguments are not compatible" >&2
		exit 1
	fi
	# this will find every tox environment matching TOX_ENV_RE and will run that
	args+=( -e "$( tox --listenvs | egrep "$TOX_ENV_RE" | tr '\n' ',' | sed -E 's/,$//' )" )
fi

set -x
tox "${args[@]}"
