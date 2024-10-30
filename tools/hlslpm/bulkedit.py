from argparse import ArgumentParser, REMAINDER
from typing import List
import github
from issue import Issue, Issues, IssueState, Status

def bulkedit_addArgs(subparsers):
    parser: ArgumentParser = subparsers.add_parser(
        'bulkedit', aliases=['be'], help='Bulk edit issues (currently hard coded)')
    parser.add_argument('--commit', action='store_true',
                       help="Commit changes to the github issues")
    
    parser.set_defaults(func=bulkEdit)

def bulkEdit(args):
    print("Fetching data...")
    
    gh = github.GH()
    issues = Issues(gh)

    # For now, hard coded to make all intrinsics issues without a status set to
    # be Planning.

    to_update : List[Issue] = [issue for issue in issues.all_issues.values() 
                               if issue.workstream == "Intrinsics" and
                               issue.issue_state == IssueState.Open and
                               issue.status == Status.NoStatus]

    print(f"Found {len(to_update)} issues.")

    if args.commit:
        for i in to_update:
            print(f"Updating {i.title}...")
            gh.set_status(i.item_id, "Planning")



