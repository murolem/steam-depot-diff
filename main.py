#!/usr/bin/env python3

import argparse
import os
from result import Result
from tabulate import tabulate
from lib.creds import clear_steam_creds_from_disk, get_steam_creds
from lib.dd import DepotDownloader, DepotInit
from lib.diff import diff
from lib.inner_binary_path import inner_binary_path

with open(inner_binary_path + 'VERSION', 'r') as file:
    VERSION = file.read().strip()

class ArgumentFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass

argparser = argparse.ArgumentParser(
                    prog='Steam Depot Differ',
                    description='Downloads app depots and diffs changes between them.',
                    epilog='Source code: https://github.com/murolem/steam-depot-diff',
                    formatter_class=ArgumentFormatter
)
argparser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')

help_table_depot_string = group2_help_table = tabulate([
    ["Steam console", """\
./depot-diff "download_depot 329130 329133 1446294067501623196" "download_depot 329130 329133 5541496194205663540"
                             ^app   ^depot ^manifest from                                     ^manifest to
    """],
    ["DepotDownloader", """\
./depot-diff "-app 329130 -depot 329133 -manifest 1446294067501623196" "-app 329130 -depot 329133 -manifest 5541496194205663540"
                   ^app          ^depot           ^manifest from                                            ^manifest to                  
"""]
], headers=["Format", "Command"], tablefmt="grid")

argparser.add_argument('app_or_depot_string_top', help=f"""\
Application ID or TOP depot string. 

If used as application ID, other positional arguments must be provided. 
Example: 722730

If used as a depot string, a string enclosed in quotes containing information about the TOP app & depot & manifest must be provided in this singular argument.
TOP meaning the depot will be applied on TOP of another depot. 
BASE string is expected as the next positional argument.
This is useful for when copying depot strings straight from SteamDB.

Examples:
NOTE: If using Steam console format and a branch depot, the branch MUST be specified with --branch
{help_table_depot_string}
""")
argparser.add_argument('depot_or_depot_string_base', help="""\
Depot ID or BASE depot string.

If used as a depot ID, other positional arguments must be provided.
Example: 799601

If used as a depot string, a string enclosed in quotes containing information about the BASE app & depot & manifest must be provided in this singular argument.
BASE meaning the other depot will be applied on TOP of this one. 
See first positional argument help for examples.
""")
argparser.add_argument('manifest_top', help="Manifest ID of manifest to diff with. Example: 5090889475431819364", nargs="?")
argparser.add_argument('manifest_base', help="Manifest ID of manifest to base the diff at. Example: 4892202388027804689", nargs="?")

group_depot = argparser.add_argument_group("DEPOTS")
group_depot.add_argument('--branch', help="Download from specified branch if available. Public by default. Takes precedence over branch specified in depot string, if any.")
group_depot.add_argument('--dd-args', help="Additional args to pass to DepotDownloader for each depot download.")
group_depot.add_argument('--depots-path', help="Directory path for storing depots.", default="depot-diff/depots")

group_dd = argparser.add_argument_group("DEPOT DOWNLOADER")
group_dd.add_argument('--dd-path', help="DepotDownloader binary directory. Created and downloaded automatically from the official repo if missing.", default=f"depot-diff/DepotDownloader")
group_dd.add_argument('--redownload-dd', help="Deletes existing DepotDownloader binary (if any) and downloads it again.", action="store_true")

group_diff = argparser.add_argument_group("DIFF")
group_diff.add_argument('--diff-path', help="Directory path for diff process. This is where the diff will happen and can be viewed.", default="depot-diff/diff")
group_diff.add_argument('--commit-diff', help="Commits the diff. May be preferred if viewing the commited changes vs uncommited is more convenient.", action="store_true")

group_creds = argparser.add_argument_group("CREDENTIALS")
group_creds.add_argument('--relogin', help="Removes any saved Steam credentials. Useful if entered wrong.", action="store_true")
group_creds.add_argument('--creds-path', help="Path to the file containing credentials.", default="depot-diff/.YOUR-CREDENTIALS-DO-NOT-SHARE")


args = argparser.parse_args()

# ================
# ==== SCRIPT ====
# ================

dd = DepotDownloader(args.dd_path, args.depots_path, args.creds_path)

depot_top: DepotInit
depot_base: DepotInit
if args.manifest_top:
    # assume positional arguments are used
    if not args.manifest_base:
        raise Exception("missing argument")

    depot_top = DepotInit(
        app=args.app_or_depot_string_top,
        depot=args.depot_or_depot_string_base,
        manifest=args.manifest_top,
        branch=args.branch or "public"
    )

    depot_base = DepotInit(
        app=args.app_or_depot_string_top,
        depot=args.depot_or_depot_string_base,
        manifest=args.manifest_base,
        branch=args.branch or "public"
    )
else:
    # assume depot strings are used

    def assert_ok(res: Result, err_msg: str):
        if res.is_err():
            print(err_msg)
            print(res.err_value.get('reason'))
            print(res.err_value)
            raise Exception("see above")

    # parse depot string
    depot_top_res = DepotDownloader.parse_depot_string(args.app_or_depot_string_top)
    depot_base_res = DepotDownloader.parse_depot_string(args.depot_or_depot_string_base)

    assert_ok(depot_top_res, "Failed to parse the TOP depot string")
    assert_ok(depot_base_res, "Failed to parse the BASE depot string")

    depot_top = depot_top_res.ok_value
    depot_base = depot_base_res.ok_value

dd.get_exec(force_download=args.redownload_dd)
print("DepotDownloader executable: " + dd.dd_exec_path)

print("Getting Steam credentials")
if args.relogin:
    clear_steam_creds_from_disk()
steam_creds = get_steam_creds(args.creds_path)
print("Will login to DepotDownloader as: " + steam_creds.login)

print("Getting depots")
print("Getting TOP depot")
depot_top_dirpath = dd.get_depot(depot_top, dd_args=args.dd_args, branch_override=args.branch)
print("Getting BASE depot")
depot_base_dirpath = dd.get_depot(depot_base, dd_args=args.dd_args, branch_override=args.branch)

# print("Diffing")
diff(args.diff_path, depot_top_dirpath, depot_base_dirpath, commit_diff=args.commit_diff)

print("All done!")
print("View diff at: " + os.path.abspath(args.diff_path))