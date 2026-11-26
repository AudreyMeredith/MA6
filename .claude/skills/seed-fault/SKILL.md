---
name: seed-fault
description: Introduce, document, and repair an intentional pipeline fault.
allowed-tools: Read, Edit, Bash
---

# Seeded fault: $ARGUMENTS

1. Read the relevant source code and verification tests.
2. Confirm the existing tests pass.
3. Introduce only the specified fault using the Edit tool.
4. Capture the PostToolUse hook stderr and failing test output.
5. Explain which test detected the fault and why.
6. Restore the original implementation without weakening tests.
7. Run make test and confirm all tests pass.
8. Append the exact change, real failure output, hook stderr,
   and repair details to docs/SEEDED_FAULTS.md.
9. Stop and let the researcher verify the evidence before committing.

Never fabricate test or hook output.
Never modify the original raw dataset.
Never change the temporal split or baselines.
