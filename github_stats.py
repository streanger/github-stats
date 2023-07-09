from typing import NamedTuple
import pandas as pd
import requests


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
    response = requests.get(api_url)
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
    for project_url in projects:
        info = gather_project_info(project_url)
        data.append(info)

    df = pd.DataFrame(data)
    df['created'] = pd.to_datetime(df['created']).dt.date
    df['updated'] = pd.to_datetime(df['updated']).dt.date
    df = df.sort_values(['stars'], ascending = [False])
    df.reset_index(drop=True, inplace=True)
    df.index += 1
    return df


if __name__ == "__main__":
    print('github-stats')
