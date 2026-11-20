# KubeGuide - Evaluation Questions

Ten representative evaluation questions from on-call site reliability engineers managing production Kubernetes clusters.

| # | Question | Document | Section / Page | Answerable? |
|---|---|---|---|---|
| 1 | Why does a Pod enter `CrashLoopBackOff` immediately after startup with exit code 137? | concepts/workloads/pods/pod-lifecycle | Container restart policy & exit codes | Yes |
| 2 | How do I migrate existing `PodSecurityPolicy` resources to `Pod Security Admission` in Kubernetes 1.25+? | reference/using-api/deprecation-guide | v1.25 PodSecurityPolicy removal | Yes |
| 3 | What causes an `ImagePullBackOff` error when pulling an image from a private container registry? | tasks/configure-pod-container/pull-image-private-registry | Registry credentials and imagePullSecrets | Yes |
| 4 | What is the recommended way to configure resource requests and limits to prevent `OOMKilled` containers? | concepts/configuration/manage-resources-containers | Resource requests, limits and OOM behavior | Yes |
| 5 | How do I troubleshoot a Kubernetes Service whose `Endpoints` list shows `<none>`? | tasks/debug/debug-application/debug-service | Service selector mismatch and endpoints | Yes |
| 6 | What will the Chennai logistics internal staging database root password be next month? | Private cluster credentials (Internal) | Not in official Kubernetes documentation | No (Unanswerable) |
| 7 | When was `networking.k8s.io/v1beta1` Ingress deprecated, and what schema changes are required for `networking.k8s.io/v1`? | reference/using-api/deprecation-guide | v1.22 Ingress deprecation & pathType | Yes |
| 8 | How does the Horizontal Pod Autoscaler compute desired replica count when scaling on memory utilization? | tasks/run-application/horizontal-pod-autoscale | HPA algorithm and target metrics | Yes |
| 9 | How should an engineer resolve a `NodeNotReady` condition triggered by `DiskPressure`? | tasks/administer-cluster/out-of-resource | Node conditions, eviction thresholds | Yes |
| 10 | What RBAC `Role` and `RoleBinding` verbs are needed for a ServiceAccount to watch ConfigMaps in a single namespace? | reference/access-authn-authz/rbac | Role, ClusterRole, and API verbs | Yes |
