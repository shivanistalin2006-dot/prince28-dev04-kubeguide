# KubeGuide - Data Sources

This document catalogs the primary source materials, formats, and licensing terms used to build the KubeGuide Kubernetes troubleshooting knowledge base.

## Target Record Fields
- `id`: Unique record identifier (e.g. `doc-k8s-001`)
- `page`: Relative path or URL slug (e.g. `tasks/debug/debug-application/debug-pods`)
- `section`: Header or anchor identifier (e.g. `CrashLoopBackOff diagnosis`)
- `k8s_version`: Target Kubernetes version (e.g. `v1.31`, `v1.30`, `v1.29`, `v1.28`)
- `object_kind`: Target Kubernetes API kind (e.g. `Pod`, `Service`, `Ingress`, `Deployment`)
- `api_version`: Target API version (e.g. `apps/v1`, `v1`, `networking.k8s.io/v1`)
- `topic`: Troubleshooting problem area (e.g. `workloads`, `networking`, `security`, `storage`)

## Sources Catalog

| Source Name | Location / URL | Format | Terms of Use / License | Notes |
|---|---|---|---|---|
| Kubernetes Website Documentation | https://github.com/kubernetes/website | Markdown / Hugo | CC BY 4.0 | Official concepts, tasks, and reference documentation |
| Deprecated API Migration Guide | https://kubernetes.io/docs/reference/using-api/deprecation-guide/ | Web page / Markdown | CC BY 4.0 | Complete guide to removed and deprecated APIs across recent versions |
| Kubernetes Release Notes (v1.28 - v1.31) | https://github.com/kubernetes/sig-release/tree/master/releases | Markdown / Text | Apache 2.0 / CC BY 4.0 | Change logs, deprecation notices, and upgrade warnings |
| Kubernetes API Reference | https://kubernetes.io/docs/reference/kubernetes-api/ | Web page / OpenAPI spec | CC BY 4.0 / Apache 2.0 | Schema specifications for workloads, networking, and cluster configs |
