# CoPilot Instructions for CCBR Repositories

## Reviewer guidance (what to look for in PRs)

- Reviewers must validate enforcement rules: no secrets, container specified, and reproducibility pins.
- If code is AI-generated, reviewers must ensure the author documents what was changed and why, and that the PR is labeled `generated-by-AI`.
- Reviewers should verify license headers and ownership metadata (for example, `CODEOWNERS`) are present.
- Reviews must read the code and verify that it adheres to the project's coding standards, guidelines, and best practices in software engineering.

## CI & enforcement suggestions (automatable)

1. **PR template**: include optional AI-assistance disclosure fields (model used, high-level prompt intent, manual review confirmation).
2. **Pre-merge check (GitHub Action)**: verify `.github/copilot-instructions.md` is present in the repository and that new pipeline files include a `# CRAFT:` header.
3. **Lint jobs**: `ruff` for Python, `shellcheck` for shell, `lintr` for R, and `nf-core lint` or Snakemake lint checks where applicable.
4. **Secrets scan**: run `TruffleHog` or `Gitleaks` on PRs to detect accidental credentials.
5. **AI usage label**: if AI usage is declared, an Action should add `generated-by-AI` label (create this label if it does not exist); the PR body should end with the italicized Markdown line: _Generated using AI_, and any associated commit messages should end with the plain footer line: `Generated using AI`.

_Sample GH Action check (concept): if AI usage is declared, require an AI-assistance disclosure field in the PR body._

## Security & compliance (mandatory)

- Developers must not send PHI or sensitive NIH internal identifiers to unapproved external AI services; use synthetic examples.
- Repository content must only be sent to model providers approved by NCI/NIH policy (for example, Copilot for Business or approved internal proxies).
- For AI-assisted actions, teams must keep an auditable record including: user, repository, action, timestamp, model name, and endpoint.
- If using a server wrapper (Option C), logs must include the minimum metadata above and follow institutional retention policy.
- If policy forbids external model use for internal code, teams must use approved local/internal LLM workflows.

## Operational notes (practical)

- `copilot-instructions.md` should remain concise and prescriptive; keep only high-value rules and edge-case examples.
- Developers should include the CRAFT block in edited files when requesting substantial generated code to improve context quality.
- CoPilot must ask the user for permission before deleting any file unless the file was created by CoPilot for a temporary run or test.
- CoPilot must not edit any files outside of the current open workspace.

## Code authoring guidance

- Code must not include hard-coded secrets, credentials, or sensitive absolute paths on disk.
- Code should be designed for modularity, reusability, and maintainability. It should ideally be platform-agnostic, with special support for running on the Biowulf HPC.
- Use pre-commit to enforce code style and linting during the commit process.

### Pipelines

- Authors must review existing CCBR pipelines first: <https://github.com/CCBR>.
- New pipelines should follow established CCBR conventions for folder layout, rule/process naming, config structure, and test patterns.
- Pipelines must define container images and pin tool/image versions for reproducibility.
- Contributions should include a test dataset and a documented example command.

#### Snakemake

- In general, new pipelines should be created with Nextflow rather than Snakemake, unless there is a compelling reason to use Snakemake.
- Generate new pipelines from the CCBR_SnakemakeTemplate repo: <https://github.com/CCBR/CCBR_SnakemakeTemplate>
- For Snakemake, run `snakemake --lint` and a dry-run before PR submission.

#### Nextflow

- Generate new pipelines from the CCBR_NextflowTemplate repo: <https://github.com/CCBR/CCBR_NextflowTemplate>
- For Nextflow pipelines, authors must follow nf-core patterns and references: <https://nf-co.re>.
- Nextflow code must use DSL2 only (DSL1 is not allowed).
- For Nextflow, run `nf-core lint` (or equivalent checks) before PR submission.
- Where possible, reuse modules and subworkflows from CCBR/nf-modules or nf-core/modules.
- New modules and subworkflows should be tested with `nf-test`.

### Python scripts and packages

- Python scripts must include module and function/class docstrings.
- Where a standard CLI framework is adopted, Python CLIs should use `click` or `typer` for consistency with existing components.
- Scripts must support `--help` and document required/optional arguments.
- Python code must follow [PEP 8](https://peps.python.org/pep-0008/), use `snake_case`, and include type hints for public functions.
- Scripts must raise descriptive error messages on failure and warnings when applicable. Prefer raising an exception over printing an error message, and over returning an error code.
- Python code should pass `ruff`;
- Each script must include a documented example usage in comments or README.
- Tests should be written with `pytest`. Other testing frameworks may be used if justified.
- Do not catch bare exceptions. The exception type must always be specified.
- Only include one return statement at the end of a function.

### R scripts and packages

- R scripts must include function and class docstrings via roxygen2.
- CLIs must be defined using the `argparse` package.
- CLIs must support `--help` and document required/optional arguments.
- R code should pass `lintr` and `air`.
- Tests should be written with `testthat`.
- Packages should pass `devtools::check()`.
- R code should adhere to the tidyverse style guide. https://style.tidyverse.org/
- Only include one return statement at the end of a function, if a return statement is used at all. Explicit returns are preferred but not required for R functions.

## AI-generated commit messages (Conventional Commits)

- Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (as enforced in `CONTRIBUTING.md`).
- Generate messages from staged changes only (`git diff --staged`); do not include unrelated work.
- Commits should be atomic: one logical change per commit.
- If mixed changes are present, split into multiple logical commits; the number of commits does not need to equal the number of files changed.
- Subject format must be: `<type>(optional-scope): short imperative summary` (<=72 chars), e.g., `fix(profile): update release table parser`.
- Add a body only when needed to explain **why** and notable impact; never include secrets, tokens, PHI, or large diffs.
- For AI-assisted commits, add this final italicized footer line in the commit message body: _commit message is ai-generated_

Suggested prompt for AI tools:

```text
Create a Conventional Commit message from this staged diff.
Rules:
1) Use one of: feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert.
2) Keep subject <= 72 chars, imperative mood, no trailing period.
3) Include optional scope when clear.
4) Add a short body only if needed (why/impact), wrapped at ~72 chars.
5) Output only the final commit message.
```

## Pull Requests

When opening a pull request, use the repository's pull request template (usually it is `.github/PULL_REQUEST_TEMPLATE.md`).
Different repos have different PR templates depending on their needs.
Ensure that the pull request follows the repository's PR template and includes all required information.
Do not allow the developer to proceed with opening a PR if it does not fill out all sections of the template.
Before a PR can be moved from draft to "ready for review", all of the relevant checklist items must be checked, and any
irrelevant checklist items should be crossed out.

When new features, bug fixes, or other behavioral changes are introduced to the code,
unit tests must be added or updated to cover the new or changed functionality.

If there are any API or other user-facing changes, the documentation must be updated both inline via docstrings and long-form docs in the `docs/` or `vignettes/` directory.

When a repo contains a build workflow (i.e. a workflow file in `.github/workflows` starting with `build` or named `R-CMD-check`),
the build workflow must pass before the PR can be approved.

### Changelog

The changelog for the repository should be maintained in a `CHANGELOG.md` file
(or `NEWS.md` for R packages) at the root of the repository. Each pull request
that introduces user-facing changes must include a concise entry with the PR
number and author username tagged. Developer-only changes (i.e. updates to CI
workflows, development notes, etc.) should never be included in the changelog.
Example:

```
## development version

- Fix bug in `detect_absolute_paths()` to ignore comments. (#123, @username)
```

## Onboarding checklist for new developers

- [ ] Read `.github/CONTRIBUTING.md` and `.github/copilot-instructions.md`.
- [ ] Configure VSCode workspace to open `copilot-instructions.md` by default (so Copilot Chat sees it).
- [ ] Install pre-commit and run `pre-commit install`.

## Appendix: VSCode snippet (drop into `.vscode/snippets/craft.code-snippets`)

```json
{
    "Insert CRAFT prompt": {
        "prefix": "craft",
        "body": [
            "/* C: Context: Repo=${workspaceFolderBasename}; bioinformatics pipelines; NIH HPC (Biowulf/Helix); containers: quay.io/ccbr */",
            "/* R: Rules: no PHI, no secrets, containerize, pin versions, follow style */",
            "/* F: Flow: inputs/ -> results/, conf/, tests/ */",
            "/* T: Tests: provide a one-line TEST_CMD and expected output */",
            "",
            "A: $1"
        ],
        "description": "Insert CRAFT prompt and place cursor at Actions"
    }
}
```
