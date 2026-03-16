# PR Review Ticket Bridge Contract

## Inputs

- pull request diff
- commits in the PR
- review comments and discussion comments
- current repo ticket contract
- current repo workflow and source-of-truth docs

## Output contract

- separate valid findings from invalid findings
- explain why each accepted finding survives review
- generate follow-up tickets only for accepted findings that are still actionable
- cite the concrete file, hunk, comment, or commit that supports the ticket

## Ticket quality rules

- one clear issue per ticket
- actionable summary
- explicit acceptance criteria
- link back to the originating PR evidence
- no duplicate tickets for already-tracked work
