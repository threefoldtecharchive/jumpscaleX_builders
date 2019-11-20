from os import path
from Jumpscale import j


class BuilderPEP8(j.baseclasses.builder):
    def prepare(self, repo_path=None):
        """ Install pre-commit hook to run autopep8 """
        j.builders.system.python_pip.install("autopep8")

        # Get git repos paths
        if repo_path is None:
            repos = (repo.BASEDIR for repo in j.clients.git.find(returnGitClient=True))
        else:
            repos = [repo_path]
        paths = (path.join(repo, ".git/hooks/pre-commit") for repo in repos)

        hook_cmd = """
        #!/bin/sh
        touched_python_files=`git diff --cached --name-only |egrep '\.py$' || true`
        if [ -n "$touched_python_files" ]; then
            autopep8 -ria --max-line-length=120 $touched_python_files
            git add $touched_python_files
        fi
        """
        for repo_path in paths:
            self._write(repo_path, hook_cmd)

    def autopep8(self, repo_path=None, commit=True, rebase=False):
        """
        Run autopep8 on found repos and commit with pep8 massage
        @param repo_path: path of desired repo to autopep8, if None will find all recognized repos to jumpscale
        @param commit: commit with pep8 as the commit message
        """
        j.builders.system.python_pip.install("autopep8")

        # Get git repos paths
        if repo_path is None:
            repos = (repo.BASEDIR for repo in j.clients.git.find(returnGitClient=True))
        else:
            repos = [repo_path]
        paths = (repo for repo in repos)

        # Prepare cmd command
        pep8_cmd = """
        #!/bin/bash
        cd {0}
        autopep8 -ria --max-line-length=120 .
        """
        commit_cmd = """
        touched_python_files=`git diff --name-only |egrep '\.py$' || true`
        if [ -n "$touched_python_files" ]; then
            git add .
            git commit -m 'pep8'
        fi
        """
        rebase_cmd = """
        git fetch
        branch=$(git symbolic-ref --short -q HEAD)
        git rebase origin/$branch
        """

        cmd = ""
        if commit is True:
            cmd = pep8_cmd + commit_cmd
            cmd += rebase_cmd if rebase else ""
        else:
            cmd = pep8_cmd

        # Execute cmd on paths
        for repo_path in paths:
            self._execute(cmd.format(repo_path), tmux=False, die=False)
