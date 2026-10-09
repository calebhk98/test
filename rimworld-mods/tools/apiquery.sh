#!/bin/sh
# Look up RimWorld 1.6 types and members. See tools/apiquery/Program.cs.
#   tools/apiquery.sh ThingDef
#   tools/apiquery.sh --find Glower
here="$(cd "$(dirname "$0")" && pwd)"
dll="$here/apiquery/bin/Debug/net8.0/apiquery.dll"
[ -f "$dll" ] || dotnet build "$here/apiquery" -nologo -v q >/dev/null || exit 1
exec dotnet "$dll" "$@"
