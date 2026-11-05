# Sources and licences

| Component | Version pinned | Licence | Use |
|---|---|---|---|
| Falco | chart `9.2.2` (Falco 0.45.x), rules artifact `falco-rules:5` | Apache-2.0 | Runtime detection sensor |
| Falco Helm chart | `9.2.2` | Apache-2.0 | Deployment |
| Minikube | `v1.34.0` in CI (`medyagh/setup-minikube@v0.0.20`) | Apache-2.0 | Local cluster |
| Kubernetes | `v1.30.0` | Apache-2.0 | Cluster |
| Alpine | `3.20` | MIT | Victim container |
| nginx | `1.27-alpine` | BSD-2-Clause | Benign workload |
| busybox | `1.36` | GPL-2.0 | Benign CronJob |
| PyYAML / pytest / ruff | `6.0.2` / `8.3.4` / `0.8.4` | MIT / MIT / MIT | Evaluation and CI |
| MITRE ATT&CK for Containers | accessed 2026-11-05 | CC BY 4.0 (ATT&CK terms) | Technique IDs only, no copied text |

No dataset or PCAP is redistributed. Every scenario is generated locally against a cluster
created by this repo; no external host is attacked. `192.0.2.1` is TEST-NET-1 (RFC 5737) and
is never reachable.
