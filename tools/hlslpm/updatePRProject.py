from argparse import ArgumentParser
from collections import namedtuple
import json
from string import Template
from datetime import datetime, date

import github


def updatePRProject_addArgs(subparsers):
    parser: ArgumentParser = subparsers.add_parser(
        'update-pr-project', aliases=['prs'])

    parser.add_argument('--commit', action='store_true',
                        help='Commit changes to github')
    parser.set_defaults(func=updatePRProject)


def updatePRProject(args):
    Updater().run(args.commit)
    pass


def updatePRItem(gh: github, item):
    pass


class Updater:
    def __init__(self):
        self.gh = github.GH()
        self.config = {
            "organizationLogin": "microsoft",
            "projectNumber": 1517
        }
        self.projectId = github.maybe_get(
            self.gh.query("prs/prs_project_id.gql", self.config),
            "data", "organization", "projectV2", "id")
        self.fields = get_fields(self.gh, self.config)

    def run(self, commit: bool):

        mutations = []

        itemCount = 0

        for item in self.gh.paged_query("prs/get_prs.gql", self.config):
            itemCount += 1
            updates = self.getUpdates(item)
            if len(updates) > 0:
                print(f"{item['content']['url']}: {
                      ' '.join([f"{k}={v}" for (k, v) in updates.items()])}")
                mutations += self.makeMutations(item, updates)
            
        if commit:
            self.update(mutations)

        print(f"{itemCount} pull requests processed.")

    def getUpdates(self, item):
        updates = {}

        pr = item['content']

        if item['pr_author'] == None:
            updates['PR Author'] = pr['author']['login']

        prCreated = get_as_date(github.maybe_get(item, 'pr_created', 'date'))
        createdAt = datetime.fromisoformat(pr['createdAt']).date()

        if prCreated != createdAt:
            updates['PR Created'] = str(createdAt)

        lastCommits = get_as_date(github.maybe_get(item, 'last_commits', 'date'))
        committedDate = datetime.fromisoformat(pr['commits']['nodes'][0]['commit']['committedDate']).date()
        if lastCommits != committedDate:
            updates['Last Commits'] = str(committedDate)

        reviewsTotalCount = pr['reviews']['totalCount']
        if item['status'] == None and reviewsTotalCount == 0:
            updates['Status'] = "Waiting for reviews"

        return updates

    def makeMutations(self, item, updates):
        return [self.makeMutation(item["id"], field, value)
                for (field, value) in updates.items()]

    def update(self, mutations):
        mutation = ["mutation() {"]
        mutation += [f"update{index}:{mutation}" for (
            index, mutation) in enumerate(mutations)]
        mutation += ["}"]

        mutation = "\n".join(mutation)
        r = self.gh.graphql(mutation)

    def makeMutation(self, itemId, fieldName, value):
        field = self.fields[fieldName]
        fieldId = field.id

        if field.dataType == "TEXT":
            valueType = "text"
        elif field.dataType == "DATE":
            valueType = "date"
        elif field.dataType == "SINGLE_SELECT":
            valueType = "singleSelectOptionId"
            value = field.options[value]

        t = "updateProjectV2ItemFieldValue( input: { "
        t += 'projectId: "$projectId" itemId: "$itemId" fieldId: "$fieldId" '
        t += 'value: {$valueType: "$value"}'
        t += "}) { clientMutationId }"
        template = Template(t)

        return template.substitute(
            {"projectId": self.projectId,
             "itemId": itemId,
             "fieldId": fieldId,
             "valueType": valueType,
             "value": value})


def get_fields(gh, config):
    fields = gh.paged_query("prs/prs_project_fields.gql", config)
    return dict([(field['name'], make_field(field)) for field in fields])


def make_field(field):
    if "options" in field:
        field["options"] = dict([(o["name"], o["id"])
                                for o in field["options"]])
    return namedtuple('field', field.keys())(*field.values())

def get_as_date(text):
    if not text:
        return None

    return date.fromisoformat(text)