# Contributing to RENEE

## Proposing changes with issues

If you want to make a change, it's a good idea to first
[open an issue](https://code-review.tidyverse.org/issues/)
and make sure someone from the team agrees that it’s needed.

If you've decided to work on an issue,
[assign yourself to the issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/assigning-issues-and-pull-requests-to-other-github-users#assigning-an-individual-issue-or-pull-request)
so others will know you're working on it.

## Pull request process

We use [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
as our collaboration process.
Follow the steps below for detailed instructions on contributing changes to
RENEE.

![GitHub Flow diagram](https://raw.githubusercontent.com/CCBR/CCBR_NextflowTemplate/main/.github/img/GitHub-Flow_bg-white.png)

### Clone the repo

If you are a member of [CCBR](https://github.com/CCBR),
you can clone this repository to your computer or development environment.
Otherwise, you will first need to
[fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
the repo and clone your fork. You only need to do this step once.

```sh
git clone https://github.com/CCBR/RENEE
```

> Cloning into 'RENEE'... <br>
> remote: Enumerating objects: 1136, done. <br>
> remote: Counting objects: 100% (463/463), done. <br>
> remote: Compressing objects: 100% (357/357), done. <br>
> remote: Total 1136 (delta 149), reused 332 (delta 103), pack-reused 673 <br>
> Receiving objects: 100% (1136/1136), 11.01 MiB | 9.76 MiB/s, done. <br>
> Resolving deltas: 100% (530/530), done. <br>

```sh
cd RENEE
```

### If this is your first time cloning the repo, you may need to install dependencies

- Install snakemake and singularity or docker if needed (biowulf already has these available as modules).

- Install the python dependencies with pip

  ```sh
  pip install .
  ```

  If you're developing on biowulf, you can use our shared conda environment which already has these dependencies installed

  ```sh
  . "/data/CCBR_Pipeliner/db/PipeDB/Conda/etc/profile.d/conda.sh"
  conda activate py311
  ```

- Install [`pre-commit`](https://pre-commit.com/#install) if you don't already
  have it. Then from the repo's root directory, run

  ```sh
  pre-commit install
  ```

  This will install the repo's pre-commit hooks.
  You'll only need to do this step the first time you clone the repo.

### Create a branch

Create a Git branch for your pull request (PR). Give the branch a descriptive
name for the changes you will make, such as `iss-10` if it is for a specific
issue.

```sh
# create a new branch and switch to it
git branch iss-10
git switch iss-10
```

> Switched to a new branch 'iss-10'

### Make your changes

Edit the code, write and run tests, and update the documentation as needed.

#### test

Changes to the **python package** code will also need unit tests to demonstrate
that the changes work as intended.
We write unit tests with pytest and store them in the `tests/` subdirectory.
Run the tests with `python -m pytest`.

If you change the **workflow**, please run the workflow with the test profile
and make sure your new feature or bug fix works as intended.

#### document

If you have added a new feature or changed the API of an existing feature,
you will likely need to update the documentation in `docs/`.

### Commit and push your changes

If you're not sure how often you should commit or what your commits should
consist of, we recommend following the "atomic commits" principle where each
commit contains one new feature, fix, or task.
Learn more about atomic commits here:
<https://www.freshconsulting.com/insights/blog/atomic-commits/>

First, add the files that you changed to the staging area:

```sh
git add path/to/changed/files/
```

Then make the commit.
Your commit message should follow the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
specification.
Briefly, each commit should start with one of the approved types such as
`feat`, `fix`, `docs`, etc. followed by a description of the commit.
Take a look at the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/#summary)
for more detailed information about how to write commit messages.

```sh
git commit -m 'feat: create function for awesome feature'
```

pre-commit will enforce that your commit message and the code changes are
styled correctly and will attempt to make corrections if needed.

> Check for added large files..............................................Passed <br>
> Fix End of Files.........................................................Passed <br>
> Trim Trailing Whitespace.................................................Failed <br>
>
> - hook id: trailing-whitespace <br>
> - exit code: 1 <br>
> - files were modified by this hook <br> > <br>
>   Fixing path/to/changed/files/file.txt <br> > <br>
>   codespell................................................................Passed <br>
>   style-files..........................................(no files to check)Skipped <br>
>   readme-rmd-rendered..................................(no files to check)Skipped <br>
>   use-tidy-description.................................(no files to check)Skipped <br>

In the example above, one of the hooks modified a file in the proposed commit,
so the pre-commit check failed. You can run `git diff` to see the changes that
pre-commit made and `git status` to see which files were modified. To proceed
with the commit, re-add the modified file(s) and re-run the commit command:

```sh
git add path/to/changed/files/file.txt
git commit -m 'feat: create function for awesome feature'
```

This time, all the hooks either passed or were skipped
(e.g. hooks that only run on R code will not run if no R files were
committed).
When the pre-commit check is successful, the usual commit success message
will appear after the pre-commit messages showing that the commit was created.

> Check for added large files..............................................Passed <br>
> Fix End of Files.........................................................Passed <br>
> Trim Trailing Whitespace.................................................Passed <br>
> codespell................................................................Passed <br>
> style-files..........................................(no files to check)Skipped <br>
> readme-rmd-rendered..................................(no files to check)Skipped <br>
> use-tidy-description.................................(no files to check)Skipped <br>
> Conventional Commit......................................................Passed <br> > [iss-10 9ff256e] feat: create function for awesome feature <br>
> 1 file changed, 22 insertions(+), 3 deletions(-) <br>

Finally, push your changes to GitHub:

```sh
git push
```

If this is the first time you are pushing this branch, you may have to
explicitly set the upstream branch:

```sh
git push --set-upstream origin iss-10
```

> Enumerating objects: 7, done. <br>
> Counting objects: 100% (7/7), done. <br>
> Delta compression using up to 10 threads <br>
> Compressing objects: 100% (4/4), done. <br>
> Writing objects: 100% (4/4), 648 bytes | 648.00 KiB/s, done. <br>
> Total 4 (delta 3), reused 0 (delta 0), pack-reused 0 <br>
> remote: Resolving deltas: 100% (3/3), completed with 3 local objects. <br>
> remote: <br>
> remote: Create a pull request for 'iss-10' on GitHub by visiting: <br>
> remote: https://github.com/CCBR/RENEE/pull/new/iss-10 <br>
> remote: <br>
> To https://github.com/CCBR/RENEE <br> > <br> > [new branch] iss-10 -> iss-10 <br>
> branch 'iss-10' set up to track 'origin/iss-10'. <br>

We recommend pushing your commits often so they will be backed up on GitHub.
You can view the files in your branch on GitHub at
`https://github.com/CCBR/RENEE/tree/<your-branch-name>`
(replace `<your-branch-name>` with the actual name of your branch).

### Create the PR

Once your branch is ready, create a PR on GitHub:
<https://github.com/CCBR/RENEE/pull/new/>

Select the branch you just pushed:

![Create a new PR from your branch](https://raw.githubusercontent.com/CCBR/CCBR_NextflowTemplate/main/.github/img/new-PR.png)

Edit the PR title and description.
The title should briefly describe the change.
Follow the comments in the template to fill out the body of the PR, and
you can delete the comments (everything between `<!--` and `-->`) as you go.
Be sure to fill out the checklist, checking off items as you complete them or
striking through any irrelevant items.
When you're ready, click 'Create pull request' to open it.

![Open the PR after editing the title and description](https://raw.githubusercontent.com/CCBR/CCBR_NextflowTemplate/main/.github/img/create-PR.png)

Optionally, you can mark the PR as a draft if you're not yet ready for it to
be reviewed, then change it later when you're ready.

### Wait for a maintainer to review your PR

We will do our best to follow the tidyverse code review principles:
<https://code-review.tidyverse.org/>.
The reviewer may suggest that you make changes before accepting your PR in
order to improve the code quality or style.
If that's the case, continue to make changes in your branch and push them to
GitHub, and they will appear in the PR.

Once the PR is approved, the maintainer will merge it and the issue(s) the PR
links will close automatically.
Congratulations and thank you for your contribution!

### After your PR has been merged

After your PR has been merged, update your local clone of the repo by
switching to the main branch and pulling the latest changes:

```sh
git checkout main
git pull
```

It's a good idea to run `git pull` before creating a new branch so it will
start from the most recent commits in main.

## Helpful links for more information

- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [semantic versioning guidelines](https://semver.org/)
- [changelog guidelines](https://keepachangelog.com/en/1.1.0/)
- [tidyverse code review principles](https://code-review.tidyverse.org)
- [reproducible examples](https://www.tidyverse.org/help/#reprex)
- [nf-core extensions for VS Code](https://marketplace.visualstudio.com/items?itemName=nf-core.nf-core-extensionpack)
