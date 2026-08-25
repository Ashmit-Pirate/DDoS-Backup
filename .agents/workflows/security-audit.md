---
description: Reviews a specified file or module against security-standards and data-integrity, and reports findings — use before merging anything touching secrets, the ML artifacts, or network config.
---

Title: Security audit
Description: Reviews a specified file or module against the
security-standards rule and reports findings.

Steps:
1. Read the specified file(s)/module.
2. Check against security-standards: hardcoded secrets, loading any .pkl
   file not trained by this team, attack-simulator traffic pointed at
   anything besides the isolated Docker network/local target, missing
   CORS lock-down, any unflagged assumption about auth.
3. Check against data-integrity: any DB write that could silently
   persist a benign flow, use a status value outside the documented
   enum, or bypass a load-bearing index.
4. If the module touches detection/, decision/, or mitigation/, check
   against ml-integration-boundaries: any direct prediction-to-block
   shortcut, any hardcoded feature list instead of loading from the .pkl
   files, an un-inverted label_mapping.
5. Report findings as a list — each with the specific line/location, why
   it's a problem, and a suggested fix. Don't fix silently unless asked.