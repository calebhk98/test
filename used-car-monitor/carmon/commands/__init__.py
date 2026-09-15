"""Command bodies and their argparse wiring, grouped by area.

`carmon/cli.py` stays the single entry point (`main`, `build_parser`); each module here
owns a handful of related subcommands — the `cmd_*` function argparse dispatches to, plus
the `add_*_parser` function that defines its flags. Keeping the two together means a flag
and the code that reads it live in the same file.
"""
