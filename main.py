import json
from functools import reduce

import datetime
import requests

global repo_name
global repo_api_url
global commits_to_analyze
global team_name
global team_members
global session_request_header

json_file = 'input.json'


def request_pulls():
    pull_requests_url = repo_api_url + '/pulls?per_page=100&status=open'
    gh_session = requests.Session()
    pulls = gh_session.get(pull_requests_url, headers=session_request_header).json()
    print('Found {} open pull requests in {}'.format(len(pulls), repo_name))
    # normalized = pd.json_normalize(pulls, max_level=2)
    # for name in normalized.columns:
    #    print(name)
    return pulls


def get_open_pr_stats():
    pulls = request_pulls()
    num_ready_prs = 0
    num_draft_prs = 0
    pulls_dict = {}

    for pr in pulls:
        print('.', end='')
        if str(pr['draft']) == 'False':
            num_ready_prs += 1
            pulls_dict[pr['number']] = filter_open_pr_info(pr)
        else:
            num_draft_prs += 1
    print()
    print('Ready PRs : {} - Draft PRs : {}'.format(num_ready_prs, num_draft_prs))
    return pulls_dict


def filter_open_pr_info(pr):
    approvals = get_approvals(str(pr['number']))
    creation_time = datetime.datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    days_since_last_approval = get_days_since_last_approval(creation_time, approvals)
    days_since_creation = get_days_since_creation(creation_time)
    return {
        'team member': is_team_member(pr['user']['login']),
        'title': pr['title'],
        'days since creation': days_since_creation,
        'days since last approval': days_since_last_approval}


def get_approvals(pr_number):
    assert isinstance(pr_number, str)
    reviews_url = repo_api_url + '/pulls/' + pr_number + '/reviews'
    gh_session = requests.Session()
    reviews_json = gh_session.get(reviews_url, headers=session_request_header).json()
    approvals = []
    for review in reviews_json:
        if review['state'] == 'APPROVED':
            approvals.append((review['user']['login'], review['submitted_at']))
    return approvals


def is_team_member(user_id):
    assert isinstance(user_id, str)
    return str(user_id in team_members)


def get_days_since_last_approval(creation_date, approvals):
    if not approvals:
        last_approval_date = creation_date
    else:
        last_approval_date = datetime.datetime.strptime(approvals[-1][1], '%Y-%m-%dT%H:%M:%SZ')
    return (datetime.datetime.now() - last_approval_date).days


def get_days_since_creation(creation_date):
    return (datetime.datetime.now() - creation_date).days


def get_pull_requests_of_last_commits():
    commits_url = repo_api_url + '/commits?per_page=' + str(commits_to_analyze)
    gh_session = requests.Session()
    commits_json = gh_session.get(commits_url, headers=session_request_header).json()
    pull_requests = {}
    print()
    print("Analyzing last {} commits".format(str(commits_to_analyze)))
    for commit in commits_json:
        print('.', end='')
        (pr_number, creation_date_str, merged_date_str) = get_prs_number_and_dates_of_commit(commit['sha'])
        creation_date = datetime.datetime.strptime(creation_date_str, '%Y-%m-%dT%H:%M:%SZ')
        merged_date = datetime.datetime.strptime(merged_date_str, '%Y-%m-%dT%H:%M:%SZ')
        pull_requests[pr_number] = {'team member': is_team_member(commit['author']['login']),
                                    'days since creation': (merged_date - creation_date).days,
                                    'days since last approval': 'not calculated'}
    print()
    return pull_requests


# Return a tuple of str dates with (creation time, merge time) for a given commit
def get_prs_number_and_dates_of_commit(commit_sha):
    pulls_url = repo_api_url + '/commits/' + commit_sha + '/pulls'
    gh_session = requests.Session()
    pulls_json = gh_session.get(pulls_url, headers=session_request_header).json()
    assert len(pulls_json) == 1
    return pulls_json[0]['number'], pulls_json[0]['created_at'], pulls_json[0]['merged_at']


# { 'PR number : { 'team member': "True", 'days since creation': 3 , 'days since last approval':1 },
#   'PR number : { 'team member': "False", 'days since creation': 2 , 'days since last approval':1 },
#   ... }
def calculate_averages(prs, use_team_prs, calculate_last_approval):
    filtered_prs = list(filter(lambda x: x['team member'] == str(use_team_prs), prs.values()))
    total_days_since_creation = reduce((lambda x, y: x + y['days since creation']), filtered_prs, 0)
    average_days_since_creation = total_days_since_creation / len(filtered_prs)

    print(' {} {} Pull Requests'.format(" No" if not use_team_prs else "", team_name))
    print('    Average days since creation =', average_days_since_creation)

    if calculate_last_approval:
        total_days_since_last_approval = reduce((lambda x, y: x + y['days since last approval']), filtered_prs, 0)
        average_days_since_last_approval = total_days_since_last_approval / len(filtered_prs)
        print('    Average days since last approval =', average_days_since_last_approval)


def parse_input_json():
    try:
        with open(json_file, 'r') as f:
            args = json.load(f)

        global repo_name
        repo_name = args['repository']

        global repo_api_url
        repo_api_url = "https://api.github.com/repos/{}".format(repo_name)

        global session_request_header
        my_token = open(args['token_file'], "r").readline().strip()
        session_request_header = {'Authorization': 'token {}'.format(my_token),
                                  'Accept': 'application/vnd.github.groot-preview+json'}

        global commits_to_analyze
        commits_to_analyze = args['commits_to_analyze']

        global team_name
        team_name = args['team_name']

        global team_members
        team_members = args['team_members']

    except IOError:
        print("Error reading file ", json_file)

    print("Script parameters:")
    print(" -Repository:", repo_name)
    print(" -Access token:", args['token_file'])
    print(" -Commits to analyze:", commits_to_analyze)
    print(" -Team name:", team_name)
    print(" -Team members:", team_members)
    print()


def main():
    parse_input_json()

    open_pr_stats = get_open_pr_stats()
    print()
    print("Stats of open PRs in", repo_name)
    # print(json.dumps(open_pr_stats))

    calculate_averages(open_pr_stats, True, True)
    calculate_averages(open_pr_stats, False, True)

    last_pr_stats = get_pull_requests_of_last_commits()
    print()
    print("Stats of last {} PRs in {}:".format(str(commits_to_analyze), repo_name))
    # print(json.dumps(last_pr_stats))

    calculate_averages(last_pr_stats, True, False)
    calculate_averages(last_pr_stats, False, False)


if __name__ == '__main__':
    main()
