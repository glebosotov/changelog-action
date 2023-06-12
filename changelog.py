import json
import os
import re

import curlify2
import httpx


def get_commit_list(url, repo, base_commit, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f'{url}/repos/{repo}/commits?sha={base_commit}'
    print(url)
    response = httpx.get(url, headers=headers, timeout=None)
    response2 = curlify2(request.request)
    print(curlify2.to_curl(response2.request))
    if response.status_code != 200:
        print(f'Error while getting commits: {response.status_code}\nURL: {url}\nResponse: {response.json()}')
        return []
    return response.json()
    
def export_summary(commits_not_in_main):

    whitelisted_commit_types = ['feat', 'fix', 'refactor', 'perf', 'chore', 'docs', 'style', 'test']

    summary_text = ''
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
    if len(summary_text) == 0:
        summary_text = 'No changes (or they do not follow conventional commit format)'
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
    gitea_token = os.environ['INPUT_GITEA_TOKEN']
    print(f'Looking for commits in Repo {repo_name} at {url}. Commit hash: {base_commit}')
    commit_list_branch = get_commit_list(url, repo_name, base_commit, gitea_token)
    commit_list = get_commit_list(url, repo_name, 'main', gitea_token)
    commits_not_in_main = [commit for commit in commit_list_branch if commit not in commit_list]
    if len(commits_not_in_main) == 0:
        ## we are in main
        latest_commit = commit_list_branch[0]
        assert len(latest_commit['parents']) <= 2, '::set-output name=changelog::Error in commit structure'
        latest = latest_commit['parents'][-1]['sha']
        oldest = latest_commit['parents'][0]['sha']
        print(latest, oldest)
        src = get_commit_list(url, repo_name, latest, gitea_token)
        if latest == oldest:
            diff = [src[0]]
        else:
            dst = get_commit_list(url, repo_name, oldest, gitea_token)
            diff = [i for i in src if i not in dst]

        commits_not_in_main = diff        

    text = (export_summary(commits_not_in_main))
    text = text.replace("\n", "\\n")
    print(f'::set-output name=changelog::{text}')
    # write to file $GITHUB_OUTPUT
    with open(os.environ['GITHUB_OUTPUT'], 'w') as f:
        text_to_write = 'changelog=' + text
        f.write(text_to_write)
