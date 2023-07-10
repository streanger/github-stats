from pathlib import Path
from typing import NamedTuple
import markdown
import pandas as pd
import requests
from rich import print


class GithubProject(NamedTuple):
    name: str
    stars: int
    watching: int
    forks: int
    issues: int
    language: str
    created: str
    updated: str
    url: str


def project_to_api_url(project_url):
    """converts github repository url to api url"""
    project_subpath = project_url.split('github.com')[-1]
    api_url = f'https://api.github.com/repos{project_subpath}'
    return api_url


def gather_project_info(project_url):
    """gather single github project info
    
    collected informations are fixed
    """
    api_url = project_to_api_url(project_url)
    response = requests.get(api_url, headers=HEADERS)
    response_json = response.json()

    # handle API limit
    message = response_json.get('message', '')
    api_limit_exceeded = "API rate limit exceeded for"
    if message.startswith(api_limit_exceeded):
        documentation_url = response_json.get('documentation_url', '')
        raise Exception(f'{message} {documentation_url}')

    # parse response
    project_info = GithubProject(
        name=response_json['name'],
        stars=response_json['stargazers_count'],  # stargazers_count -> stars
        watching=response_json['subscribers_count'],  # subscribers_count -> watching
        forks=response_json['forks'],
        issues=response_json['open_issues'],
        language=response_json['language'],
        created=response_json['created_at'],
        updated=response_json['updated_at'],
        url=project_url
    )
    return project_info


def projects_to_df(projects):
    """get projects info and store it as dataframe
    
    projects - list[project_url]
    """
    data = []
    total = len(projects)
    for index, project_url in enumerate(projects, start=1):
        print(f'{index}/{total}) {project_url}')
        info = gather_project_info(project_url)
        data.append(info)

    df = pd.DataFrame(data)
    df['created'] = pd.to_datetime(df['created']).dt.date
    df['updated'] = pd.to_datetime(df['updated']).dt.date
    df = df.sort_values(
        ['stars', 'watching', 'forks', 'issues', 'created', 'updated'],
        ascending = [False, False, False, False, False, False]
    )
    df.reset_index(drop=True, inplace=True)
    df.index += 1
    return df


def list_repos(user):
    """list all public github repos for specific user"""
    blank_url = 'https://api.github.com/users/{}/repos?page={}'
    repos_json_total = []
    repos_urls = []
    page = 1
    while True:
        url = blank_url.format(user, page)
        response = requests.get(url, headers=HEADERS)
        repos_json = response.json()
        if not repos_json:
            break
        repos_json_total.extend(repos_json)
        respos_urls_page = [item['clone_url'] for item in repos_json]
        repos_urls.extend(respos_urls_page)
        page += 1
    return repos_json_total, repos_urls


if __name__ == "__main__":
    # set your api token
    # to create token go to: https://github.com/settings/tokens
    TOKEN = input('your Github token (you can skip, and use default limits): ')
    if TOKEN.strip():
        HEADERS = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28"
            }
    else:
        HEADERS = None

    # get github stats
    repos_json_total, repos_urls = list_repos('streanger')
    repos_urls = [item.removesuffix('.git') for item in repos_urls]
    df = projects_to_df(repos_urls)
    df.to_csv('projects.csv')
    md = df.to_markdown()
    Path('projects.md').write_text(md)
    print(md)

    # html table
    table_html = markdown.markdown(md, extensions=['markdown.extensions.tables'])
    Path('index.html').write_text(table_html)
