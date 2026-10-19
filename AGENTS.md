# Repository guidance

This public repository maintains only `github-sync`, `ch584-ui-tuning`, and `embedded-link-debug`, their reference files, and local packaging tools.

- Inspect relevant skill and reference files before editing. Keep the skill entry point concise and put detailed cases in references.
- Keep source inspection, build/test results, flashing, and observed hardware results separate. Historical project evidence is not current hardware verification.
- Preserve installed skill changes. Installation may copy missing skills and skip byte-identical skills, but must refuse conflicting content before writing anything. Do not add force overwrite or mutate global instructions/configuration.
- Do not add credentials, private conversations, account snapshots, whole Codex configuration, source-project backups, or private repository history. Project-specific historical paths may appear only as explicitly bounded evidence, never as installation defaults.
- Use project-local `.local` for disposable tests. Run `python -B tools/Verify-Repository.py` and `python -B -m unittest discover -s tests -v` after relevant changes; tests require PowerShell 7.
- Review the final diff. Do not install globally, flash hardware, publish, commit or push unless authorized by the user or applicable standing instructions.
