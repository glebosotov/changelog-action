import os
import re

import httpx


def get_commit_list(url, repo, base_commit, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'{url}/api/v1/repos/{repo}/commits?sha={base_commit}'
    print(url)
    response = httpx.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json()
    
def export_summary(commits_not_in_main):

    whitelisted_commit_types = ['feat', 'fix', 'refactor', 'perf', 'chore', 'docs', 'style', 'test']

    summary_text = 'Changes since last release:\n'
    for commit in commits_not_in_main:
        commit_message = commit['commit']['message']
        # if commit message does not follow conventional commit format, skip it
        if ':' not in commit_message:
            continue
        commit_type = commit_message.split(':')[0]
        if commit_type in whitelisted_commit_types:
            summary_text += f'\n - {commit_message}'
    # set max length to 500
    summary_text = summary_text[:500]
    return summary_text

if __name__ == '__main__':
    url = os.environ['GITHUB_API_URL']
    repo_name = os.environ['GITHUB_REPOSITORY']
    base_commit = os.environ['INPUT_BASE']
    gitea_token = os.environ['INPUT_GITEA-TOKEN']
    commit_list_branch = get_commit_list(url, repo_name, base_commit, gitea_token)
    commit_list = get_commit_list(url, repo_name, 'main', gitea_token)
    commits_not_in_main = [commit for commit in commit_list_branch if commit not in commit_list]

    print(export_summary(commits_not_in_main))
