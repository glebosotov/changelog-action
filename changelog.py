import os
import re

import httpx


def get_commit_list(url, repo, base_commit, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'{url}/repos/{repo}/commits?sha={base_commit}'
    # print(url)
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
    try:
        import dotenv
        dotenv.load_dotenv()
    except ModuleNotFoundError:
        pass
    url = os.environ['GITHUB_API_URL']
    repo_name = os.environ['GITHUB_REPOSITORY']
    base_commit = os.environ['GITHUB_SHA']
    gitea_token = os.environ['INPUT_GITEA-TOKEN']
    commit_list_branch = get_commit_list(url, repo_name, base_commit, gitea_token)
    commit_list = get_commit_list(url, repo_name, 'main', gitea_token)
    # commit_shas = [commit['sha'] for commit in commit_list]
    commits_not_in_main = [commit for commit in commit_list_branch if commit not in commit_list]

    if len(commits_not_in_main) == 0:
        ## we are in main
        latest_commit = commit_list_branch[0]
        assert len(latest_commit['parents']) == 2, '::set-output name=changelog::Error in commit structure'
        latest = latest_commit['parents'][1]['sha']
        oldest = latest_commit['parents'][0]['sha']
        oldest_index = [i for i, commit in enumerate(commit_list) if commit['sha'] == oldest][0]
        latest_index = [i for i, commit in enumerate(commit_list) if commit['sha'] == latest][0]
        commits_not_in_main = commit_list[oldest_index:latest_index]

    text = (export_summary(commits_not_in_main))
    text = text.replace('\n', '\\n')
    # print(len(commits_not_in_main))
    print(f'::set-output name=changelog::{text}')
