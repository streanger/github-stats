from pathlib import Path
import sys
from typing import NamedTuple

import pandas as pd
import pwinput
import requests
from rich import print


HEADERS = None

class GithubProject(NamedTuple):
    name: str
    stars: int
    watching: int
    forks: int
    issues: int
    language: str
    created: str
    updated: str
    alive: bool
    url: str


def project_to_api_url(project_url):
    """converts github repository url to api url"""
    project_subpath = project_url.split('github.com')[-1]
    api_url = f'https://api.github.com/repos{project_subpath}'
    return api_url


def bad_credentials_error(github_api_response):
    """raise exception if bad credentials for github api passed"""
    if type(github_api_response) is not dict:
        return
    if github_api_response.get('message', '') == 'Bad credentials':
        docs = github_api_response.get('documentation_url', '')
        raise Exception(f'Bad credentials, go to: {docs}')


def gather_project_info(project_url):
    """gather single github project info
    
    collected informations are fixed
    """
    api_url = project_to_api_url(project_url)
    response = requests.get(api_url, headers=HEADERS)
    response_json = response.json()
    bad_credentials_error(response_json)

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
        alive=(not response_json['archived']),
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
        ['stars', 'watching', 'forks', 'issues', 'created', 'updated', 'alive'],
        ascending = [False, False, False, False, False, False, False]
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
        bad_credentials_error(repos_json)
        if not repos_json:
            break
        repos_json_total.extend(repos_json)
        respos_urls_page = [item['clone_url'] for item in repos_json]
        repos_urls.extend(respos_urls_page)
        page += 1
    return repos_json_total, repos_urls


def projects_by_topic(topic):
    """get projects by topic
    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-topics
    https://stackoverflow.com/questions/51912862/how-to-list-all-repositories-for-a-given-topic-with-rest-api-in-github
    """
    url = f'https://api.github.com/search/repositories?q=topic:{topic}'
    response = requests.get(url)
    projects = response.json()['items']

    # parse data
    data = []
    total = len(projects)
    for index, project_json in enumerate(projects, start=1):
        print(f"{index}/{total}) {project_json['html_url']}")
        project_info = GithubProject(
            name=project_json['name'],
            stars=project_json['stargazers_count'],  # stargazers_count -> stars
            watching=project_json['watchers_count'],  # watchers_count is the same as stargazers_count. It seems that is a problem on github api side
            forks=project_json['forks'],
            issues=project_json['open_issues'],
            language=project_json['language'],
            created=project_json['created_at'],
            updated=project_json['updated_at'],
            alive=(not project_json['archived']),
            url=project_json['html_url'],
        )
        data.append(project_info)

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


def to_html(header, table):
    """convert table with list of lists to html table

    from sets_matcher.py, modified to fit
    """
    tab = ' '*4
    table_head = '\n'.join([f"{tab*4}<th><button>{column}</button></th>" for column in header])
    table_body = ""
    for row in table:
        cells = []
        for index, column in enumerate(row):
            if index and (type(column) is int) and (column > 0):
                # cell_style = "style=\"background-color: #eeeeee; border-radius: 10px;\""
                # column = "✓"
                cell_class = 'class="marker"'
            elif str(column).startswith('https://github.com'):
                column = f"<a href=\"{column}\">{column}</a>"
                cell_class = ""
            else:
                cell_class = ""
            cells.append(f"{tab*5}<td {cell_class}>{column}</td>\n")
        cells = ''.join(cells)
        table_body += f"{tab*4}<tr>\n{cells}{tab*4}</tr>\n"
    table_body = table_body.rstrip()

    style = '''\
        .styled-table {
            border-collapse: collapse;
            margin-left: auto;
            margin-right: auto;
            font-size: 0.8em;
            font-family: sans-serif;
            min-width: 400px;
        }
        .styled-table thead tr {
            background-color: #009879;
            color: #ffffff;
        }
        .styled-table td {
            padding: 6px 9px;
            text-align: center;
        }
        .styled-table td:first-child {
            padding: 6px 9px;
            text-align: right;
        }
        .styled-table td:last-child {
            padding: 6px 9px;
            text-align: left;
        }
        .styled-table tbody tr {
            border-bottom: 1px solid #dddddd;
        }
        .styled-table th {
            padding: 0;
            text-align: center;
        }
        .styled-table th button {
            background-color: transparent;
            border: none;
            font: inherit;
            color: inherit;
            height: 100%;
            width: 100%;
            padding: 6px 9px;
            display: inline-block;
        }
        .styled-table th button::after {
            content: "\\00a0\\00a0";
            font-family: 'Courier New', Courier, monospace
        }
        .styled-table th button[direction="ascending"]::after {
            content: " ▲";
        }
        .styled-table th button[direction="descending"]::after {
            content: " ▼";
        }
        .marker {
        background-color: #eeeeee;
        border-radius: 10px;
        }'''

    script = """\
// https://webdesign.tutsplus.com/how-to-create-a-sortable-html-table-with-javascript--cms-92993t
// https://css-tricks.com/almanac/selectors/a/after-and-before/
// https://stackoverflow.com/questions/2965229/nbsp-not-working-in-css-content-tag
// https://stackoverflow.com/questions/7790811/how-do-i-put-variables-inside-javascript-strings

function main() {
    var table = document.getElementsByTagName("table")[0];
    var header = table.getElementsByTagName("tr")[0];
    var headers = header.getElementsByTagName("th");
    for (var i = 0; i < headers.length; i++) {
        var btn = headers[i].getElementsByTagName("button")[0];
        btn.setAttribute("onclick", `table_sorter(${i})`);
    }
}

function table_sorter(column) {
    var table = document.getElementsByTagName("table")[0];
    var tableBody = table.getElementsByTagName("tbody")[0];
    var columnButton = table.getElementsByTagName("tr")[0].getElementsByTagName("th")[column].getElementsByTagName("button")[0];
    var direction = columnButton.getAttribute("direction");
    if (direction == "ascending") {
        direction = "descending";
    } else {
        direction = "ascending";
    }
    var rows = Array.from(table.getElementsByTagName("tr")).slice(1);
    rows.sort(function(a, b) {
        var x = a.getElementsByTagName("td")[column].textContent.toLowerCase();
        var y = b.getElementsByTagName("td")[column].textContent.toLowerCase();
        if (direction === "ascending") {
            // try to sort numbers
            return x - y || x.localeCompare(y);
        } else {
            // try to sort numbers
            return y - x || y.localeCompare(x);
        }
    });
    rows.forEach(function(row) {
        tableBody.appendChild(row);
    });

    // show direction using arrow icon
    var header = table.getElementsByTagName("tr")[0];
    var headers = header.getElementsByTagName("th");
    for (var i = 0; i < headers.length; i++) {
        var btn = headers[i].getElementsByTagName("button")[0];
        if (i == column) {
            btn.setAttribute("direction", direction);
        } else {
            btn.setAttribute("direction", "");
        }
    }
}"""

    template = f"""\
<html>
    <head>
        <title>sets matcher</title>
        <meta charset="utf-8">
        <style>
{style}
        </style>
        <script>
{script}
        </script>
    </head>
    <body onload=main()>
        <table class="styled-table">
            <thead>
                <tr>
{table_head}
                </tr>
            </thead>
            <tbody>
{table_body}
            </tbody>
        </table>
    </body>
</html>\
"""
    return template


if __name__ == "__main__":
    # set your api token
    # to create token go to: https://github.com/settings/tokens
    TOKEN = pwinput.pwinput(prompt='your Github token (you can skip, and use default limits): ')
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
    del df['alive']  # for my projects it is always True as for now

    # write to csv
    csv_out = 'projects.csv'
    df.to_csv(csv_out)
    print()
    print(f'saved to: [green]{csv_out}')

    # write to markdown
    md = df.to_markdown()
    markdown_out = 'projects.md'
    Path(markdown_out).write_text(md, encoding='utf-8')
    print(f'saved to: [green]{markdown_out}')

    # write to html
    df = df.reset_index(names=['index'])
    header, table = df.columns, df.values.tolist()
    html = to_html(header, table)
    html_out = 'index.html'
    Path(html_out).write_text(html, encoding='utf-8')
    print(f'saved to: [green]{html_out}')

    # print markdown
    print()
    print(md)
