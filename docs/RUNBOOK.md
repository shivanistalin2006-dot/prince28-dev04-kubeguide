# SRE Runbook: Kubernetes Incident Troubleshooting

This runbook guides on-call site reliability engineers through diagnosing and remediating common production incidents across Kubernetes clusters.

---

## 1. Fast Triage Workflow (First 5 Minutes)

When an alert triggers, execute these commands in sequence to establish situational awareness:

```bash
# 1. Check pod status across all namespaces
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# 2. Inspect cluster events ordered by timestamp
kubectl get events -A --sort-by='.lastTimestamp' | tail -n 25

# 3. Check node health and conditions
kubectl get nodes -o wide
```

---

## 2. Common Failure Modes & Remediation

### A. `CrashLoopBackOff`
* **Symptoms:** Pod starts, crashes repeatedly, and the restart counter steadily increases.
* **Triage steps:**
  ```bash
  # Check current crash logs
  kubectl logs <pod-name> -n <namespace>

  # Check previous container crash logs (crucial for quick crashes)
  kubectl logs <pod-name> -n <namespace> --previous

  # Inspect exit code and termination reason
  kubectl describe pod <pod-name> -n <namespace>
  ```
* **Exit code guide:**
  * **Exit Code 137:** Out Of Memory (OOMKilled). Container exceeded its memory limit.
    * *Fix:* Increase `resources.limits.memory` in the pod spec or profile application memory consumption.
  * **Exit Code 1 / 2:** Application startup failure, unhandled runtime exception, or invalid configuration.
    * *Fix:* Validate environment variables, ConfigMaps, and Secret bindings.
  * **Exit Code 143:** Graceful SIGTERM received from Kubernetes (e.g., node drain, liveness probe failure).

---

### B. `ImagePullBackOff` & `ErrImagePull`
* **Symptoms:** Container cannot start because the container runtime cannot fetch the specified image.
* **Triage steps:**
  ```bash
  kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Events
  ```
* **Root causes:**
  1. **Typo in image name or tag:** Verify tag matches container registry release tags.
  2. **Missing `imagePullSecrets`:** For private registries, verify that the secret exists in the target namespace and is linked to the ServiceAccount.
  3. **Registry rate limiting or network timeout:** Verify node egress to container registry endpoints.

---

### C. `Pending` Pods
* **Symptoms:** Pod remains in `Pending` phase without being scheduled to any worker node.
* **Triage steps:**
  ```bash
  kubectl describe pod <pod-name> -n <namespace>
  ```
* **Root causes & checks:**
  * **Insufficient CPU/Memory:** Look for `0/N nodes available: Insufficient cpu`.
    * *Fix:* Check cluster autoscaler or downscale non-critical deployments.
  * **Taints and Tolerations:** Check if nodes have taints that the pod lacks tolerations for.
  * **Unbound PersistentVolumeClaim:** Verify PVC status (`kubectl get pvc -n <namespace>`).

---

### D. `NodeNotReady`
* **Symptoms:** Node condition `Ready=False` or `Ready=Unknown`.
* **Triage steps:**
  ```bash
  # Inspect node conditions and disk/memory pressure
  kubectl describe node <node-name>

  # SSH to node and verify kubelet status
  systemctl status kubelet
  journalctl -u kubelet -n 50 --no-pager
  ```

---

## 3. Escalation Checklist
- [ ] Confirm customer-facing impact and update status page.
- [ ] Capture pod logs and describe outputs before restarting or scaling deployments.
- [ ] Check deployment revision history (`kubectl rollout history deployment/<name>`).
- [ ] Roll back if incident was triggered by a recent release:
  ```bash
  kubectl rollout undo deployment/<name> -n <namespace>
  ```
