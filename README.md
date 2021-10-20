
Script to compare pull requests statistics of a team of collaborators on a given Github repository.

The script will show two different statistics:

- For all open pull requests (discarding drafts):
  - Average days since creation, for the team and the rest
  - Average days since last approval, for the team and the rest
    
- For the last commits (defined by `commits_to_analyze` field in `input.json`) on the repo:
  - Average days since creation to merging, for the team and the rest


Script expects a `input.json` file with the configuration. The following variables are needed:

- `repository` : the Github repository (with the format `user/repository`) to be analyzed
- `token_file` : file containing your Github personal access token (More info: [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token))
- `commits_to_analyze` : number of merged commits to analyze
- `team_name` : a name for the team you are getting the stats about
- `team_members` : list of the team Github user names

You can find a template at `input_template. json`.

Json file example:
```
{
  "repository": "cool_sw_company/big_sw_project",
  "token_file": "mytoken.txt",
  "commits_to_analyze": "50",
  "team_name": "dev_team1"
  "team_members" : ["the_backender", "the_frontender", "the_intern"]
}
```

Sample output:

```
$ python team-pr-stats/main.py
Script parameters:
 -Repository : cool_sw_company/big_sw_project
 -Access token: mytoken.txt
 -Commits to analyze: 50
 -Team name: dev_team1
 -Team members: ["the_backender", "the_frontender", "the_intern"]

Found 47 open pull requests in cool_sw_company/big_sw_project
...............................................
Ready PRs : 20 - Draft PRs : 27

Stats of open PRs in cool_sw_company/big_sw_project:
  dev_team1 Pull Requests
    Average days since creation = 97.44444444444444
    Average days since last approval = 82.55555555555556
  No dev_team1 Pull Requests
    Average days since creation = 15.909090909090908
    Average days since last approval = 12.090909090909092

Analyzing last 30 commits
..............................

Stats of last 30 PRs in cool_sw_company/big_sw_project:
  dev_team1 Pull Requests
    Average days since creation = 18.333333333333332
  No dev_team1 Pull Requests
    Average days since creation = 2.72

```


