# Dataset: KubeGuide

A Kubernetes assistant for on-call engineers that explains errors, objects and kubectl output from the official docs for the cluster's version.

- **Start target:** Concepts + tasks pages (about 700 pages)
- **Full target:** + reference + release notes for 4 versions (2,500+ pages)
- **Collected by:** `scripts/fetch.py` as `examate-student-bot` (https://github.com/shivanistalin2006-dot/prince28-dev04-kubeguide): robots.txt respected, at most 4 requests at once, 0.5 s between requests to one site.

## Where the documents come from

- https://github.com/kubernetes/website
- https://kubernetes.io/docs/reference/using-api/deprecation-guide/

## Terms I follow

Kubernetes docs CC BY 4.0.
- Every answer links to the original document.
- No personal data is collected.

<!-- generated:start -->
## Sources (generated 2026-11-23 09:10 UTC by scripts/dataset_report.py)

| Source | Licence / terms | Files | MB | Pages* | How | Fetched | Example URL |
|---|---|---|---|---|---|---|---|
| k8s-docs | Kubernetes docs CC BY 4.0. | 412 | 4.1 | 1,340 | git @ bc2d2df8e3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/_index.md |
| kubernetes-io | CC BY 4.0 | 10 | 5.6 | 166 | http | 2026-11-23 | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ |

**Total:** 422 files, 9.7 MB, 1,505 pages. Not downloaded: 0 blocked by robots.txt, 0 failed.

*Pages = PDF pages, plus one page per 3,000 characters of text or HTML.

## Files (first 200 of 422)

The complete list, with a sha256 fingerprint of every file, is `data/manifest.jsonl`.

| # | Title / file | Source | Pages | Fetched | URL |
|---|---|---|---|---|---|
| 1 | content/en/docs/concepts/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/_index.md |
| 2 | content/en/docs/concepts/architecture/_index.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/_index.md |
| 3 | content/en/docs/concepts/architecture/cgroups.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/cgroups.md |
| 4 | content/en/docs/concepts/architecture/cloud-controller.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/cloud-controller.md |
| 5 | content/en/docs/concepts/architecture/control-plane-node-communication.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/control-plane-node-communication.md |
| 6 | content/en/docs/concepts/architecture/controller.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/controller.md |
| 7 | content/en/docs/concepts/architecture/garbage-collection.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/garbage-collection.md |
| 8 | content/en/docs/concepts/architecture/leases.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/leases.md |
| 9 | content/en/docs/concepts/architecture/mixed-version-proxy.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/mixed-version-proxy.md |
| 10 | content/en/docs/concepts/architecture/nodes.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/nodes.md |
| 11 | content/en/docs/concepts/architecture/self-healing.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/architecture/self-healing.md |
| 12 | content/en/docs/concepts/cluster-administration/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/_index.md |
| 13 | content/en/docs/concepts/cluster-administration/addons.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/addons.md |
| 14 | content/en/docs/concepts/cluster-administration/admission-webhooks-good-practices.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/admission-webhooks-good-practices.md |
| 15 | content/en/docs/concepts/cluster-administration/certificates.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/certificates.md |
| 16 | content/en/docs/concepts/cluster-administration/compatibility-version.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/compatibility-version.md |
| 17 | content/en/docs/concepts/cluster-administration/coordinated-leader-election.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/coordinated-leader-election.md |
| 18 | content/en/docs/concepts/cluster-administration/dra.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/dra.md |
| 19 | content/en/docs/concepts/cluster-administration/flow-control.md | k8s-docs | 14 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/flow-control.md |
| 20 | content/en/docs/concepts/cluster-administration/kube-state-metrics.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/kube-state-metrics.md |
| 21 | content/en/docs/concepts/cluster-administration/logging.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/logging.md |
| 22 | content/en/docs/concepts/cluster-administration/networking.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/networking.md |
| 23 | content/en/docs/concepts/cluster-administration/node-autoscaling.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/node-autoscaling.md |
| 24 | content/en/docs/concepts/cluster-administration/node-shutdown.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/node-shutdown.md |
| 25 | content/en/docs/concepts/cluster-administration/observability.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/observability.md |
| 26 | content/en/docs/concepts/cluster-administration/proxies.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/proxies.md |
| 27 | content/en/docs/concepts/cluster-administration/swap-memory-management.md | k8s-docs | 7 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/swap-memory-management.md |
| 28 | content/en/docs/concepts/cluster-administration/system-logs.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/system-logs.md |
| 29 | content/en/docs/concepts/cluster-administration/system-metrics.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/system-metrics.md |
| 30 | content/en/docs/concepts/cluster-administration/system-traces.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/cluster-administration/system-traces.md |
| 31 | content/en/docs/concepts/configuration/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/_index.md |
| 32 | content/en/docs/concepts/configuration/configmap.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/configmap.md |
| 33 | content/en/docs/concepts/configuration/manage-resources-containers.md | k8s-docs | 12 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/manage-resources-containers.md |
| 34 | content/en/docs/concepts/configuration/organize-cluster-access-kubeconfig.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/organize-cluster-access-kubeconfig.md |
| 35 | content/en/docs/concepts/configuration/secret.md | k8s-docs | 11 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/secret.md |
| 36 | content/en/docs/concepts/configuration/windows-resource-management.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/configuration/windows-resource-management.md |
| 37 | content/en/docs/concepts/containers/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/_index.md |
| 38 | content/en/docs/concepts/containers/container-environment.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/container-environment.md |
| 39 | content/en/docs/concepts/containers/container-lifecycle-hooks.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/container-lifecycle-hooks.md |
| 40 | content/en/docs/concepts/containers/cri.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/cri.md |
| 41 | content/en/docs/concepts/containers/images.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/images.md |
| 42 | content/en/docs/concepts/containers/runtime-class.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/containers/runtime-class.md |
| 43 | content/en/docs/concepts/extend-kubernetes/_index.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/_index.md |
| 44 | content/en/docs/concepts/extend-kubernetes/api-extension/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/api-extension/_index.md |
| 45 | content/en/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation.md |
| 46 | content/en/docs/concepts/extend-kubernetes/api-extension/custom-resources.md | k8s-docs | 7 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/api-extension/custom-resources.md |
| 47 | content/en/docs/concepts/extend-kubernetes/compute-storage-net/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/compute-storage-net/_index.md |
| 48 | content/en/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins.md |
| 49 | content/en/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins.md |
| 50 | content/en/docs/concepts/extend-kubernetes/operator.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/extend-kubernetes/operator.md |
| 51 | content/en/docs/concepts/overview/_index.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/_index.md |
| 52 | content/en/docs/concepts/overview/components.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/components.md |
| 53 | content/en/docs/concepts/overview/kubectl.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/kubectl.md |
| 54 | content/en/docs/concepts/overview/kubernetes-api.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/kubernetes-api.md |
| 55 | content/en/docs/concepts/overview/working-with-objects/_index.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/_index.md |
| 56 | content/en/docs/concepts/overview/working-with-objects/annotations.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/annotations.md |
| 57 | content/en/docs/concepts/overview/working-with-objects/common-labels.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/common-labels.md |
| 58 | content/en/docs/concepts/overview/working-with-objects/field-selectors.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/field-selectors.md |
| 59 | content/en/docs/concepts/overview/working-with-objects/finalizers.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/finalizers.md |
| 60 | content/en/docs/concepts/overview/working-with-objects/labels.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/labels.md |
| 61 | content/en/docs/concepts/overview/working-with-objects/names.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/names.md |
| 62 | content/en/docs/concepts/overview/working-with-objects/namespaces.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/namespaces.md |
| 63 | content/en/docs/concepts/overview/working-with-objects/object-management.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/object-management.md |
| 64 | content/en/docs/concepts/overview/working-with-objects/owners-dependents.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/owners-dependents.md |
| 65 | content/en/docs/concepts/overview/working-with-objects/storage-version.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/overview/working-with-objects/storage-version.md |
| 66 | content/en/docs/concepts/policy/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/policy/_index.md |
| 67 | content/en/docs/concepts/policy/limit-range.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/policy/limit-range.md |
| 68 | content/en/docs/concepts/policy/pid-limiting.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/policy/pid-limiting.md |
| 69 | content/en/docs/concepts/policy/resource-quotas.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/policy/resource-quotas.md |
| 70 | content/en/docs/concepts/resource-management/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/_index.md |
| 71 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/_index.md |
| 72 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/device-taints.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/device-taints.md |
| 73 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-api.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-api.md |
| 74 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-features.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-features.md |
| 75 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-observability.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/dra-observability.md |
| 76 | content/en/docs/concepts/resource-management/dynamic-resource-allocation/how-dra-works.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/dynamic-resource-allocation/how-dra-works.md |
| 77 | content/en/docs/concepts/resource-management/effective-pod-requests-limits.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/effective-pod-requests-limits.md |
| 78 | content/en/docs/concepts/resource-management/pod-level-resource-managers.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/pod-level-resource-managers.md |
| 79 | content/en/docs/concepts/resource-management/resource-managers.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/resource-management/resource-managers.md |
| 80 | content/en/docs/concepts/scheduling-eviction/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/_index.md |
| 81 | content/en/docs/concepts/scheduling-eviction/api-eviction.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/api-eviction.md |
| 82 | content/en/docs/concepts/scheduling-eviction/assign-pod-node.md | k8s-docs | 11 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/assign-pod-node.md |
| 83 | content/en/docs/concepts/scheduling-eviction/gang-scheduling.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/gang-scheduling.md |
| 84 | content/en/docs/concepts/scheduling-eviction/kube-scheduler.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/kube-scheduler.md |
| 85 | content/en/docs/concepts/scheduling-eviction/node-declared-features.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/node-declared-features.md |
| 86 | content/en/docs/concepts/scheduling-eviction/node-pressure-eviction.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/node-pressure-eviction.md |
| 87 | content/en/docs/concepts/scheduling-eviction/pod-overhead.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/pod-overhead.md |
| 88 | content/en/docs/concepts/scheduling-eviction/pod-priority-preemption.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/pod-priority-preemption.md |
| 89 | content/en/docs/concepts/scheduling-eviction/pod-scheduling-readiness.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/pod-scheduling-readiness.md |
| 90 | content/en/docs/concepts/scheduling-eviction/podgroup-scheduling.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/podgroup-scheduling.md |
| 91 | content/en/docs/concepts/scheduling-eviction/resource-bin-packing.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/resource-bin-packing.md |
| 92 | content/en/docs/concepts/scheduling-eviction/running-multiple-schedulers.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/running-multiple-schedulers.md |
| 93 | content/en/docs/concepts/scheduling-eviction/scheduler-perf-tuning.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/scheduler-perf-tuning.md |
| 94 | content/en/docs/concepts/scheduling-eviction/scheduling-framework.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/scheduling-framework.md |
| 95 | content/en/docs/concepts/scheduling-eviction/taint-and-toleration.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/taint-and-toleration.md |
| 96 | content/en/docs/concepts/scheduling-eviction/topology-aware-scheduling.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/topology-aware-scheduling.md |
| 97 | content/en/docs/concepts/scheduling-eviction/topology-spread-constraints.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/topology-spread-constraints.md |
| 98 | content/en/docs/concepts/scheduling-eviction/workload-aware-preemption.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/scheduling-eviction/workload-aware-preemption.md |
| 99 | content/en/docs/concepts/security/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/_index.md |
| 100 | content/en/docs/concepts/security/api-server-bypass-risks.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/api-server-bypass-risks.md |
| 101 | content/en/docs/concepts/security/application-security-checklist.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/application-security-checklist.md |
| 102 | content/en/docs/concepts/security/cloud-native-security.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/cloud-native-security.md |
| 103 | content/en/docs/concepts/security/controlling-access.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/controlling-access.md |
| 104 | content/en/docs/concepts/security/hardening-guide/authentication-mechanisms.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/hardening-guide/authentication-mechanisms.md |
| 105 | content/en/docs/concepts/security/hardening-guide/dynamic-resource-allocation.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/hardening-guide/dynamic-resource-allocation.md |
| 106 | content/en/docs/concepts/security/hardening-guide/scheduler.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/hardening-guide/scheduler.md |
| 107 | content/en/docs/concepts/security/linux-kernel-security-constraints.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/linux-kernel-security-constraints.md |
| 108 | content/en/docs/concepts/security/linux-security.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/linux-security.md |
| 109 | content/en/docs/concepts/security/multi-tenancy.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/multi-tenancy.md |
| 110 | content/en/docs/concepts/security/pod-security-admission.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/pod-security-admission.md |
| 111 | content/en/docs/concepts/security/pod-security-policy.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/pod-security-policy.md |
| 112 | content/en/docs/concepts/security/pod-security-standards.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/pod-security-standards.md |
| 113 | content/en/docs/concepts/security/rbac-good-practices.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/rbac-good-practices.md |
| 114 | content/en/docs/concepts/security/secrets-good-practices.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/secrets-good-practices.md |
| 115 | content/en/docs/concepts/security/security-checklist.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/security-checklist.md |
| 116 | content/en/docs/concepts/security/service-accounts.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/service-accounts.md |
| 117 | content/en/docs/concepts/security/windows-security.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/security/windows-security.md |
| 118 | content/en/docs/concepts/services-networking/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/_index.md |
| 119 | content/en/docs/concepts/services-networking/cluster-ip-allocation.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/cluster-ip-allocation.md |
| 120 | content/en/docs/concepts/services-networking/dns-pod-service.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/dns-pod-service.md |
| 121 | content/en/docs/concepts/services-networking/dual-stack.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/dual-stack.md |
| 122 | content/en/docs/concepts/services-networking/endpoint-slices.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/endpoint-slices.md |
| 123 | content/en/docs/concepts/services-networking/gateway.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/gateway.md |
| 124 | content/en/docs/concepts/services-networking/ingress-controllers.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/ingress-controllers.md |
| 125 | content/en/docs/concepts/services-networking/ingress.md | k8s-docs | 10 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/ingress.md |
| 126 | content/en/docs/concepts/services-networking/network-policies.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/network-policies.md |
| 127 | content/en/docs/concepts/services-networking/service-traffic-policy.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/service-traffic-policy.md |
| 128 | content/en/docs/concepts/services-networking/service.md | k8s-docs | 16 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/service.md |
| 129 | content/en/docs/concepts/services-networking/topology-aware-routing.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/topology-aware-routing.md |
| 130 | content/en/docs/concepts/services-networking/windows-networking.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/services-networking/windows-networking.md |
| 131 | content/en/docs/concepts/storage/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/_index.md |
| 132 | content/en/docs/concepts/storage/dynamic-provisioning.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/dynamic-provisioning.md |
| 133 | content/en/docs/concepts/storage/ephemeral-storage.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/ephemeral-storage.md |
| 134 | content/en/docs/concepts/storage/ephemeral-volumes.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/ephemeral-volumes.md |
| 135 | content/en/docs/concepts/storage/persistent-volumes.md | k8s-docs | 17 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/persistent-volumes.md |
| 136 | content/en/docs/concepts/storage/projected-volumes.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/projected-volumes.md |
| 137 | content/en/docs/concepts/storage/storage-capacity.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/storage-capacity.md |
| 138 | content/en/docs/concepts/storage/storage-classes.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/storage-classes.md |
| 139 | content/en/docs/concepts/storage/storage-limits.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/storage-limits.md |
| 140 | content/en/docs/concepts/storage/volume-attributes-classes.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-attributes-classes.md |
| 141 | content/en/docs/concepts/storage/volume-health-monitoring.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-health-monitoring.md |
| 142 | content/en/docs/concepts/storage/volume-populators-and-data-sources.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-populators-and-data-sources.md |
| 143 | content/en/docs/concepts/storage/volume-pvc-datasource.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-pvc-datasource.md |
| 144 | content/en/docs/concepts/storage/volume-snapshot-classes.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-snapshot-classes.md |
| 145 | content/en/docs/concepts/storage/volume-snapshots.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volume-snapshots.md |
| 146 | content/en/docs/concepts/storage/volumes.md | k8s-docs | 11 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/volumes.md |
| 147 | content/en/docs/concepts/storage/windows-storage.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/storage/windows-storage.md |
| 148 | content/en/docs/concepts/windows/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/windows/_index.md |
| 149 | content/en/docs/concepts/windows/intro.md | k8s-docs | 7 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/windows/intro.md |
| 150 | content/en/docs/concepts/windows/user-guide.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/windows/user-guide.md |
| 151 | content/en/docs/concepts/workloads/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/_index.md |
| 152 | content/en/docs/concepts/workloads/autoscaling.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/autoscaling.md |
| 153 | content/en/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale.md | k8s-docs | 12 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale.md |
| 154 | content/en/docs/concepts/workloads/autoscaling/vertical-pod-autoscale.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/autoscaling/vertical-pod-autoscale.md |
| 155 | content/en/docs/concepts/workloads/compositepodgroup-api/_index.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/compositepodgroup-api/_index.md |
| 156 | content/en/docs/concepts/workloads/compositepodgroup-api/lifecycle.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/compositepodgroup-api/lifecycle.md |
| 157 | content/en/docs/concepts/workloads/controllers/_index.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/_index.md |
| 158 | content/en/docs/concepts/workloads/controllers/cron-jobs.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/cron-jobs.md |
| 159 | content/en/docs/concepts/workloads/controllers/daemonset.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/daemonset.md |
| 160 | content/en/docs/concepts/workloads/controllers/deployment.md | k8s-docs | 20 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/deployment.md |
| 161 | content/en/docs/concepts/workloads/controllers/job.md | k8s-docs | 22 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/job.md |
| 162 | content/en/docs/concepts/workloads/controllers/replicaset.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/replicaset.md |
| 163 | content/en/docs/concepts/workloads/controllers/replicationcontroller.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/replicationcontroller.md |
| 164 | content/en/docs/concepts/workloads/controllers/statefulset.md | k8s-docs | 9 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/statefulset.md |
| 165 | content/en/docs/concepts/workloads/controllers/ttlafterfinished.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/controllers/ttlafterfinished.md |
| 166 | content/en/docs/concepts/workloads/management.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/management.md |
| 167 | content/en/docs/concepts/workloads/podgroup-api/_index.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/podgroup-api/_index.md |
| 168 | content/en/docs/concepts/workloads/podgroup-api/lifecycle.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/podgroup-api/lifecycle.md |
| 169 | content/en/docs/concepts/workloads/pods/_index.md | k8s-docs | 9 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/_index.md |
| 170 | content/en/docs/concepts/workloads/pods/advanced-pod-config.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/advanced-pod-config.md |
| 171 | content/en/docs/concepts/workloads/pods/disruptions.md | k8s-docs | 6 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/disruptions.md |
| 172 | content/en/docs/concepts/workloads/pods/downward-api.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/downward-api.md |
| 173 | content/en/docs/concepts/workloads/pods/ephemeral-containers.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/ephemeral-containers.md |
| 174 | content/en/docs/concepts/workloads/pods/init-containers.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/init-containers.md |
| 175 | content/en/docs/concepts/workloads/pods/pod-condition.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/pod-condition.md |
| 176 | content/en/docs/concepts/workloads/pods/pod-hostname.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/pod-hostname.md |
| 177 | content/en/docs/concepts/workloads/pods/pod-lifecycle.md | k8s-docs | 16 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/pod-lifecycle.md |
| 178 | content/en/docs/concepts/workloads/pods/pod-qos.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/pod-qos.md |
| 179 | content/en/docs/concepts/workloads/pods/pod-termination.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/pod-termination.md |
| 180 | content/en/docs/concepts/workloads/pods/probes.md | k8s-docs | 8 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/probes.md |
| 181 | content/en/docs/concepts/workloads/pods/scheduling-group.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/scheduling-group.md |
| 182 | content/en/docs/concepts/workloads/pods/sidecar-containers.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/sidecar-containers.md |
| 183 | content/en/docs/concepts/workloads/pods/static-pods.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/static-pods.md |
| 184 | content/en/docs/concepts/workloads/pods/user-namespaces.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/pods/user-namespaces.md |
| 185 | content/en/docs/concepts/workloads/workload-api/_index.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/workload-api/_index.md |
| 186 | content/en/docs/concepts/workloads/workload-api/disruption-and-priority.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/workload-api/disruption-and-priority.md |
| 187 | content/en/docs/concepts/workloads/workload-api/policies.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/workload-api/policies.md |
| 188 | content/en/docs/concepts/workloads/workload-api/topology-aware-scheduling.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/workload-api/topology-aware-scheduling.md |
| 189 | content/en/docs/concepts/workloads/workload-api/workloadbuilder.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/concepts/workloads/workload-api/workloadbuilder.md |
| 190 | content/en/docs/tasks/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/_index.md |
| 191 | content/en/docs/tasks/access-application-cluster/_index.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/_index.md |
| 192 | content/en/docs/tasks/access-application-cluster/access-cluster-services.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/access-cluster-services.md |
| 193 | content/en/docs/tasks/access-application-cluster/access-cluster.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/access-cluster.md |
| 194 | content/en/docs/tasks/access-application-cluster/communicate-containers-same-pod-shared-volume.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/communicate-containers-same-pod-shared-volume.md |
| 195 | content/en/docs/tasks/access-application-cluster/configure-access-multiple-clusters.md | k8s-docs | 4 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/configure-access-multiple-clusters.md |
| 196 | content/en/docs/tasks/access-application-cluster/configure-access-single-cluster.md | k8s-docs | 5 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/configure-access-single-cluster.md |
| 197 | content/en/docs/tasks/access-application-cluster/configure-dns-cluster.md | k8s-docs |  | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/configure-dns-cluster.md |
| 198 | content/en/docs/tasks/access-application-cluster/connecting-frontend-backend.md | k8s-docs | 3 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/connecting-frontend-backend.md |
| 199 | content/en/docs/tasks/access-application-cluster/create-external-load-balancer.md | k8s-docs | 2 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/create-external-load-balancer.md |
| 200 | content/en/docs/tasks/access-application-cluster/list-all-running-container-images.md | k8s-docs | 1 | 2026-11-23 | https://github.com/kubernetes/website/blob/HEAD/content/en/docs/tasks/access-application-cluster/list-all-running-container-images.md |
<!-- generated:end -->

## Known gaps

- Release notes and deprecated API migration guides for the remaining 3 previous versions will be added in the full corpus phase.
- Reference documentation for API groups outside core workloads (e.g. specialized CRDs) are excluded from the start target.
