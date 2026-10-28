#!/usr/bin/env bash
# Official standalone route only. No mirrors, proxy changes or verification bypass.
set -euo pipefail

blender_version="${1:-4.2.23}"
blender_tools_dir="${2:-/workspace/.tools/blender-official}"
if [[ ! "$blender_version" =~ ^4\.2\.[0-9]+$ ]]; then
  printf 'Expected a Blender 4.2 LTS patch version.\n' >&2
  exit 2
fi

blender_archive="blender-${blender_version}-linux-x64.tar.xz"
blender_base_url='https://download.blender.org/release/Blender4.2'
mkdir -p "$blender_tools_dir/downloads"
cd "$blender_tools_dir/downloads"

# Preserve inherited HTTPS_PROXY and CA trust. A destination denial is a blocker.
curl --fail --show-error --location --proto '=https' --proto-redir '=https' \
  --connect-timeout 20 --max-time 60 \
  --output "blender-${blender_version}.sha256" \
  "$blender_base_url/blender-${blender_version}.sha256"
curl --fail --show-error --location --proto '=https' --proto-redir '=https' \
  --connect-timeout 20 \
  --output "$blender_archive.part" "$blender_base_url/$blender_archive"

python3 - "$blender_archive" "blender-${blender_version}.sha256" <<'PY'
import hashlib,re,sys
from pathlib import Path
archive_name,checksum_name=sys.argv[1:]
expected=[]
for line in Path(checksum_name).read_text().splitlines():
    fields=line.split()
    if len(fields)==2 and fields[1].lstrip('*')==archive_name:
        if not re.fullmatch(r'[0-9a-fA-F]{64}',fields[0]):
            raise SystemExit('Invalid SHA256 checksum format')
        expected.append(fields[0].lower())
if len(expected)!=1:
    raise SystemExit('Official checksum list must identify exactly this archive')
digest=hashlib.sha256()
with Path(archive_name+'.part').open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024*1024),b''):
        digest.update(block)
if digest.hexdigest()!=expected[0]:
    raise SystemExit('Blender archive checksum mismatch; refusing extraction')
Path(archive_name+'.part').replace(archive_name)
print('Official Blender archive SHA256 verified')
PY

tar --extract --xz --file "$blender_archive" --directory "$blender_tools_dir"
"$blender_tools_dir/blender-${blender_version}-linux-x64/blender" --version
