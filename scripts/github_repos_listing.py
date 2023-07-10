import os
import json
import requests
from pathlib import Path
from rich import print


"""
useful:
    https://api.github.com/
    https://stackoverflow.com/questions/8713596/how-to-retrieve-the-list-of-all-github-repositories-of-a-person
"""


def write_json(filename, data):
    """write to json file"""
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)
    return True
    
    
def list_repos(user):
    blank_url = 'https://api.github.com/users/{}/repos?page={}'
    repos_json_total = []
    repos_urls = []
    page = 1
    while True:
        url = blank_url.format(user, page)
        response = requests.get(url)
        repos_json = response.json()
        if not repos_json:
            break
        repos_json_total.extend(repos_json)
        respos_urls_page = [item['clone_url'] for item in repos_json]
        repos_urls.extend(respos_urls_page)
        page += 1
    return repos_json_total, repos_urls
    
    
if __name__ == "__main__":
    os.chdir(str(Path(__file__).parent))
    
    # ******** get repos data ********
    user = 'streanger'
    repos_json_total, repos_urls = list_repos(user)
    print(repos_urls)
    
    # ******** write repos info to json ********
    json_file = '{}_github_repos.json'.format(user)
    write_json(json_file, repos_json_total)
    print('[*] json saved to: {}'.format(json_file))
    
    # ******** print git clone commands ********
    commands = ['git clone {}'.format(url) for url in repos_urls]
    commands_str = '\n'.join(commands) + '\n'
    print('[*] commands to clone repositories:')
    print(commands_str)
    