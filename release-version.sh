#!/usr/bin/env bash
tag=$1
if echo ${tag} | grep -qe '^[0-9]\+\.[0-9]\+\.[0-9]\+$'
then
    echo "Format OK"
else
    echo "Version number does not match required format: 0.0.0"
    exit 1
fi
sed -Ei "s/__version__ = '[0-9]+\.[0-9]+\.[0-9]+'/__version__ = '$tag'/" chsimpy/version.py
grep -E "__version__ = '[0-9]+\.[0-9]+\.[0-9]+'" chsimpy/version.py || exit 1
git add chsimpy/version.py || exit 1
git commit --amend --no-edit || exit 1
git tag -a ${tag} -m "Release version ${tag}" || exit 1
curr_branch=`git rev-parse --abbrev-ref HEAD`
git checkout main && git merge ${curr_branch} --ff-only && git checkout ${curr_branch}
echo "Done."
