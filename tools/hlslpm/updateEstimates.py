# Sets Estimate field from the Complexity field
from argparse import ArgumentParser
import github


def updateEstimates_addArgs(subparsers):
    parser: ArgumentParser = subparsers.add_parser(
        'update-estimates', aliases=['ue'])

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--commit', action='store_true',
                       help='Commit changes to the github issues')
    parser.set_defaults(func=updateEstimates)


def updateEstimates(args):
    gh = github.GH()

    complexityFieldInfo = gh.get_project_field_info("Complexity")
    estimateFieldInfo = gh.get_project_field_info("Estimate")

    mapping = {
        '1': 'Hours', 
        '2': 'Days', 
        '3': 'Days', 
        '5': 'Days', 
        '8': 'Sprint', 
        '13': 'Multiple Sprints', 
        '21': 'Multiple Sprints', 
        '50': 'Break Up', 
        'n/a': 'n/a'
    }

    mapping = dict([(complexityFieldInfo["options"][c], estimateFieldInfo["options"][e]) for (c,e) in mapping.items()])

    complexityIdToName = dict([(id, name) for (name, id) in complexityFieldInfo["options"].items()])
    estimateIdToName = dict([(id, name) for (name, id) in estimateFieldInfo["options"].items()])


    currentData = gh.paged_query('gql/get_complexity_estimate.gql', {})

    warned = False
    for i in currentData:
        if not warned and github.maybe_get(i, "content") == None:
            print("Looks like PAT doesn't SSO configured - go to https://github.com/settings/tokens and click Configure SSO to access Microsoft project items.")
            warned = True

        complexity = github.maybe_get(i, "complexity", "optionId")
        if complexity and not github.maybe_get(i, "estimate", "optionId"):
            resourcePath = github.maybe_get(i, "content", "resourcePath")

            estimate = mapping[complexity]

            print(f"https://github.com{resourcePath} {complexityIdToName[complexity]} --> {estimateIdToName[estimate]}")
            if args.commit:
                gh.set_project_field(estimateFieldInfo["projectId"], i["id"], estimateFieldInfo["fieldId"], estimate)


