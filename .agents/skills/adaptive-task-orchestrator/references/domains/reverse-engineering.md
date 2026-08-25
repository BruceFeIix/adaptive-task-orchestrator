# Reverse Engineering Domain Policy

Read this reference for binary analysis, decompiler output, IDA/Ghidra work, protocol or state recovery, vulnerability reasoning, or key/flag/patch claims. Keep all analysis and execution within the user's authorized scope.

## Start with Deterministic Evidence

Use tools before language models for facts they can extract reliably:

- file hash, architecture, format, sections, segments, and entry points;
- imports, exports, strings, constants, relocations, and signatures;
- functions, callers, callees, cross-references, and call graph;
- basic blocks, control-flow edges, data references, and pseudocode;
- known library, runtime, compiler, or algorithm signatures;
- available traces, test vectors, debugger observations, and sample inputs.

Do not ask an expensive model to rediscover an import table or mechanically summarize every function. Preserve addresses, symbols, and artifact identities so later conclusions remain traceable.

## Decompose by Semantic Contour

Prefer logical function clusters over one-worker-per-function:

- entry, dispatcher, and command-processing paths;
- parsing and data-structure recovery;
- validation, encoding, hashing, or cryptographic paths;
- state machine and lifecycle transitions;
- anti-debugging, environment checks, or obfuscation;
- input/output, persistence, or network boundaries;
- candidate decoys and unrelated library/runtime code.

Use the call graph bottom-up where practical: known signatures and leaf helpers first, then their callers, then cross-cluster synthesis. A function's size is only one signal. Small functions with indirect calls, global state, pointer aliasing, wide arithmetic, or caller-dependent semantics may be difficult.

Parallelize independent read-only contours. Workers may propose names, types, comments, or patches, but a single writer applies changes to a shared IDA/Ghidra database. Database copies or isolated outputs must be explicit before allowing parallel mutation.

## Route by Evidence Burden

| Work | Default capability | Escalation signals |
|---|---|---|
| imports, strings, xrefs, inventory, fixed-schema function summaries | `fast_reader` | ambiguous identity or contradictory references |
| known wrappers and obvious leaf utilities | `fast_reader` or `general_worker` | caller context changes semantics |
| ordinary function clusters, data flow, structures, common algorithms | `general_worker` | indirect flow, lost types, or cross-cluster state |
| cross-function state, unusual protocols, compiler artifacts, difficult roots | `deep_reasoner` | weak oracle or competing global explanations |
| crypto, anti-debug, VM/obfuscation, exploitability, final key/flag/patch chain | `deep_reasoner` plus `frontier_reviewer` | always require evidence-focused independent review |

Reading pseudocode is not automatically cheap. Raise the route for complex aliasing, undefined behavior, exception flow, concurrency, ABI dependence, optimizer-distorted types, self-modifying code, opaque predicates, indirect calls, custom crypto, or global invariants.

## Evidence Model

Classify every material statement:

- `OBSERVED`: directly supported by disassembly, pseudocode, xref, memory, trace, or tool output;
- `INFERRED`: best explanation of multiple observations, with alternatives considered;
- `HYPOTHESIS`: plausible but missing decisive evidence.

For each key claim require as applicable:

```yaml
claim:
classification: OBSERVED | INFERRED | HYPOTHESIS
location:
  binary_hash:
  address_or_symbol:
  caller_or_xref:
evidence:
counterevidence_or_alternatives:
confidence: high | medium | low
verification:
  trace | test_vector | reimplementation | debugger | unresolved
```

Bound code excerpts to what supports the claim. Do not treat decompiler syntax as ground truth when types, calling convention, signedness, integer width, or aliasing are uncertain. Check assembly or dynamic behavior when those details change the conclusion.

## Verification and Review

Use the strongest available oracle appropriate to the claim:

1. known signature or deterministic constant relationship;
2. cross-reference and caller/callee consistency;
3. reimplementation against test vectors;
4. controlled debugger or trace observation;
5. independent static reconstruction when execution is unavailable.

A final flag, key, algorithm, vulnerability, exploitability, or patch claim requires an end-to-end evidence chain and independent review. Model agreement is not verification. A reviewer should receive the relevant binary identity, task contract, raw locations, traces, and candidate result, then actively seek a counterexample or alternate path.

Do not execute an unknown binary, attach to a live target, patch a binary, or use network interaction unless that action is within the user's authorization and the environment is appropriately isolated. Analysis permission does not imply permission to deploy or exploit.

## Replan and Stop Conditions

Replan when:

- a presumed independent contour shares state or a dispatcher with another;
- a library signature or compiler artifact invalidates prior naming;
- a trace contradicts static control flow;
- the decompiler omitted a critical type or indirect target;
- a decoy or anti-analysis path was mistaken for the real path.

Stop short of a definitive conclusion when critical code, version identity, trace provenance, or verification material is unavailable. Return verified facts, conditional conclusions, competing hypotheses, and the smallest additional artifact or experiment needed to decide.
