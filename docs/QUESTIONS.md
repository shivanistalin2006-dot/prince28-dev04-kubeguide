# KubeGuide - Evaluation Questions

Ten representative evaluation questions from on-call site reliability engineers managing production Kubernetes clusters.

1. Why does a Pod enter `CrashLoopBackOff` immediately after startup with exit code 137?
2. How do I migrate existing `PodSecurityPolicy` resources to `Pod Security Admission` in Kubernetes 1.25+?
3. What causes an `ImagePullBackOff` error when pulling an image from a private container registry?
4. What is the recommended way to configure resource requests and limits to prevent `OOMKilled` containers?
5. How do I troubleshoot a Kubernetes Service whose `Endpoints` list shows `<none>`?
6. What will the Chennai logistics internal staging database root password be next month? (Unanswerable: Private secret not present in Kubernetes documentation)
7. When was `networking.k8s.io/v1beta1` Ingress deprecated, and what schema changes are required for `networking.k8s.io/v1`?
8. How does the Horizontal Pod Autoscaler compute desired replica count when scaling on memory utilization?
9. How should an engineer resolve a `NodeNotReady` condition triggered by `DiskPressure`?
10. What RBAC `Role` and `RoleBinding` verbs are needed for a ServiceAccount to watch ConfigMaps in a single namespace?
