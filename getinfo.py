from github_stats import projects_to_df
from pathlib import Path
from rich import print

projects = [
    "https://github.com/ansible/ansible",
    "https://github.com/docker/compose",
    "https://github.com/kubernetes/kubernetes",
    "https://github.com/hashicorp/terraform",
    "https://github.com/hashicorp/vagrant",
    "https://github.com/travis-ci/travis-ci",
    "https://github.com/moby/moby",
    "https://github.com/jenkinsci/jenkins",
    "https://github.com/buildbot/buildbot",
    "https://github.com/pulumi/pulumi",
]

purpose_mapping = {
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

df = projects_to_df(projects)
df['purpose'] = df['url'].map(purpose_mapping)  # additional column
df.to_csv('projects.csv')
md = df.to_markdown()
Path('projects.md').write_text(md)
print(md)
