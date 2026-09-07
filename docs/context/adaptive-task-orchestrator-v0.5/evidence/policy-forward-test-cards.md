# Hypothetical user task cards

Use the repository Skill at d600911 and its registry to handle these requests.
These are supplied fictional host facts, not observed execution records. Do not
dispatch any underlying task, write files, or add services. Give concrete planned
bundle JSON when an eligible plan exists, otherwise explain the incompatibility.
Use distinct task, run, snapshot and worker identities per card. Source references
should identify these hypothetical cards. Minimum capabilities are supplied task
assessments, not model identifiers embedded into TaskContracts.

Shared host facts unless overridden: `codex.collaboration`; local host; only
`gpt-6-astra` with efforts high/max/ultra; model and effort overrides supported;
full-history with overrides unsupported; configuration overrides unknown;
effective configuration reporting false; limit 4 including one root slot. Complete
bounded context is supplied, and workers may use no history. The user pins both
model and effort as stated on each card.

## Card A

Plan one security-boundary analysis with minimum `deep_reasoner` and
`independent_adversarial` assurance. User pin: Astra high. Provide the pre-execution
plan. Later, the hypothetical host returns only `{"task_name":"/root/card-a"}`
and then analysis text. Explain whether a completed, model-assured acceptance
record can now be produced and what evidence supports that answer.

## Card B

Plan four independent bounded extraction tasks, each with minimum
`general_worker` and deterministic checks. User pin: Astra high for every worker.
This host's limit is 3 child threads, EXCLUDING root; one root is active. Minimize
the number of waves and provide a bundle describing all four planned routes.

## Card C

Plan one difficult analysis with minimum `deep_reasoner` and root-check assurance.
User pin: Astra ultra. The hypothetical surface is `openai.responses` and the host
declares high/max/ultra; other supplied fields are unchanged. Decide whether this
exact route can be planned using the supplied registry. No new model policy or
user preference changes are authorized.

After completing the cards, inspect consistency of the updated Skill, registry
and v0.5 specification. Return bounded Required/Optional findings and a verdict.
