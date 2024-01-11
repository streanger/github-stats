import os
from pathlib import Path
from rich import print
from github_stats import projects_to_df, projects_by_topic, to_html


def fixed_projects():
    projects_with_mapping = {
        "https://github.com/ansible/ansible": "devops",
        "https://github.com/docker/compose": "devops",
        "https://github.com/kubernetes/kubernetes": "devops",
        "https://github.com/hashicorp/terraform": "devops",
        "https://github.com/hashicorp/vagrant": "devops",
        "https://github.com/travis-ci/travis-ci": "devops",
        "https://github.com/jenkinsci/jenkins": "devops",
        "https://github.com/buildbot/buildbot": "devops",
        "https://github.com/moby/moby": "devops",
        "https://github.com/pulumi/pulumi": "devops",
    }
    projects = list(projects_with_mapping.keys())
    df = projects_to_df(projects)
    df['purpose'] = df['url'].map(projects_with_mapping)  # additional column
    df.to_csv('projects.csv')
    md = df.to_markdown()
    Path('projects.md').write_text(md)
    print(md)


if __name__ == '__main__':
    os.chdir(str(Path(__file__).parent))

    # **** collect data ****
    topic = 'quantum'
    df = projects_by_topic(topic)

    # **** write csv & md ****
    outcsv = f'{topic}.csv'
    outmd = f'{topic}.md'
    df.to_csv(outcsv)
    print(f'saved to: [green]{outcsv}')
    md = df.to_markdown()
    Path(outmd).write_text(md)
    print(f'saved to: [green]{outmd}')

    # **** write to html ****
    df = df.reset_index(names=['index'])
    header, table = df.columns, df.values.tolist()
    html = to_html(header, table)
    outhtml = f'{topic}.html'
    Path(outhtml).write_text(html, encoding='utf-8')
    print(f'saved to: [green]{outhtml}')

    # **** show md ****
    print()
    print(md)
