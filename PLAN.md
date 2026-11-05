# PLAN — k8s-threat-detection-lab

## Goal
Measure how well Falco's default runtime rules detect 15 container attack scenarios on a
self-hosted Kubernetes cluster (Minikube), then add custom rules for what the defaults miss.
Report v1 (defaults only) vs v2 (defaults + custom), and false alerts during a benign workload.

## Ground truth
`scenarios/expected.yaml` is written and committed **before** the first evaluation run.
It lists, for every scenario, the rule names (any of) that count as a detection.

## Design
- Minikube (docker driver, 1 node), namespace `lab` for victims, `falco` for the sensor.
- Falco installed with Helm, modern eBPF driver, JSON output; alerts collected from the
  Falco pod log (`kubectl logs -f`).
- `scripts/run_scenarios.sh` runs each `scenarios/S*.sh` in order and writes the start/end
  timestamps to `results/timeline.tsv`.
- `evaluate.py` joins the timeline with the alerts, computes:
  - per-scenario detection in v1 (alert rule not defined in `rules/custom_rules.yaml`)
    and v2 (any alert, default or custom)
  - alerts during the benign window, per hour
  - a per-rule table and a scenario x rule matrix
- CI runs lint + unit tests on every push, and the full lab on demand / on main.

## Time box
2-3 hours of authoring. The heavy run happens on GitHub Actions; no local Docker is available.

## Honest limitations (to keep in README)
- One-node Minikube is not a production cluster.
- 15 scenarios is a sample, not a benchmark.
- Falco's default ruleset evolves; versions are pinned and recorded.
- The benign window is short, so "alerts/hour" has a wide confidence interval.
