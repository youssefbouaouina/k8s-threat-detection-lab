# Interview notes — k8s-threat-detection-lab

## What this project demonstrates

- Building a detection lab end to end: Minikube, a victim workload, 15 scripted attack
  scenarios, a 15-minute benign workload, Falco alerts collected as JSONL, and an evaluator
  that attributes every alert to a scenario window.
- Writing ground truth before the first run (`scenarios/expected.yaml`) and gating on it.
- Measuring both sides of detection: recall against the scenarios and alerts/hour during the
  benign window.
- Writing Falco rules in the modern condition syntax and proving they fire, instead of copying
  rules without evidence.
- Documenting a negative result. The default chart installs only the stable `falco-rules`
  feed; several expected container rules live in the incubating, sandbox or Kubernetes-audit
  feeds, so the absolute recall is lower than the scenario list suggests. The README reports
  the gap and the gate only requires v2 not to be worse than v1.

## Questions I expect

**Why not use the full Falco rules registry?**
A detection lab should measure the artifact a reader actually gets from a default install. The
chart's `falco-rules` artifact is that default. Enabling incubating/sandbox rules would raise
the score but change the question to "how good is Falco with every optional feed". The missing
rules are named in `RESULTS.md` so the gap is visible.

**How do you avoid counting a delayed alert against the next scenario?**
Each scenario has a start and end timestamp; the evaluator only counts alerts in its own window
plus a fixed grace period. The first version used 4 seconds and alerts from S12 landed in S13,
so the settle time was raised to 12 seconds and the attribution was re-checked. That is the
kind of bug that makes a detection score meaningless.

**Why Minikube and not a managed cluster?**
Cost and reproducibility. A one-node Minikube with the modern eBPF driver exercises the same
Falco syscall path, and the whole lab can run in GitHub Actions. The limitation (no managed
control plane, no audit webhook) is stated rather than hidden.

**What do the custom rules add?**
Five rules for behaviours the default feed did not cover in this environment: service-account
token reads, downloads to `/tmp`, API-server contact from a container, and similar. They are
identified by name, so v1 (default only) and v2 (default + custom) can be computed from one
run.

**What would you do with more time?**
Add the k8saudit plugin and API-server audit webhook for control-plane techniques, replay the
same scenarios against a managed cluster for a reality check, and extend the benign workload
to several hours so the alerts/hour interval is narrower. All three are listed as limitations.

**What is the most useful number in the report?**
Not the recall percentage: the benign alert rate. A rule set that catches every scenario but
pages 200 times an hour is unusable. The report puts both numbers side by side.
