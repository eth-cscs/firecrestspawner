## f7t4jhub: FirecREST for JupyterHub Helm Chart 

This is a repository for a Helm chart to deploy JupyterHub using the [firecrestspawner](https://github.com/eth-cscs/firecrestspawner).

### Fetching the repository

```bash
helm repo add f7t4jhub https://eth-cscs.github.io/firecrestspawner
helm repo update
```

The available versions can be listed with

```bash
helm search repo f7t4jhub/f7t4jhub --versions
```

### Deploying the chart

```bash
helm install --create-namespace <deployment-name> -n<namespace> f7t4jhub/f7t4jhub --values values.yaml
```
