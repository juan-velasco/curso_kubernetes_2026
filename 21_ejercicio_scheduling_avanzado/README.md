# Ejercicio: Scheduling avanzado de Pods con PodAntiAffinity

## Objetivo

Desplegar una aplicación nginx distribuida entre los nodos del clúster usando `PodAntiAffinity`. La regla garantiza que **como máximo un Pod de este Deployment se ejecute en cada nodo**, usando la etiqueta `workload: HighResourceUsage` como selector.

Se incluyen dos manifiestos que demuestran los dos modos de anti-affinity:

| Fichero | Modo | Comportamiento si no se puede cumplir |
|---|---|---|
| `deployment_required.yaml` | `requiredDuringSchedulingIgnoredDuringExecution` | El Pod queda en `Pending` |
| `deployment_preferred.yaml` | `preferredDuringSchedulingIgnoredDuringExecution` | El Pod se programa igualmente |

## Requisitos previos

- Minikube instalado y en ejecución
- Al menos 2 nodos en el clúster (ver pasos a continuación)
- `kubectl` configurado

## Pasos

### 1. Añadir nodos a Minikube

Por defecto Minikube arranca con un solo nodo. Para ver la distribución real, necesitamos al menos 2:

```bash
minikube node add
minikube node add   # opcional: añadir un tercero para 3 réplicas
```

Verificar los nodos disponibles:

```bash
kubectl get nodes
```

### 2. Aplicar los Deployments

```bash
kubectl apply -f deployment_required.yaml
kubectl apply -f deployment_preferred.yaml
```

### 3. Verificar la distribución entre nodos

```bash
kubectl get pods -o wide
```

La columna `NODE` debe mostrar nodos distintos para cada Pod.

Con `required` y menos nodos que réplicas, los Pods extra quedarán en `Pending`.  
Con `preferred`, todos los Pods se programarán aunque no se pueda respetar la distribución ideal.

### 4. Experimentar

**Escalar réplicas para ver Pods en Pending (modo required):**

```bash
kubectl scale deployment nginx-anti-affinity-required --replicas=5
kubectl get pods -o wide
```

**Escalar réplicas para ver que no quedan Pending (modo preferred):**

```bash
kubectl scale deployment nginx-anti-affinity-preferred --replicas=5
kubectl get pods -o wide
```

**Eliminar los Deployments al terminar:**

```bash
kubectl delete -f deployment_required.yaml
kubectl delete -f deployment_preferred.yaml
```

## Explicación de los manifiestos

### Modo required

```yaml
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
          - key: workload
            operator: In
            values:
              - HighResourceUsage
      topologyKey: "kubernetes.io/hostname"
```

La regla es **obligatoria**. Si no hay nodo disponible que la cumpla, el Pod queda en `Pending` indefinidamente.

### Modo preferred

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
            - key: workload
              operator: In
              values:
                - HighResourceUsage
        topologyKey: "kubernetes.io/hostname"
```

La regla es una **preferencia** con peso 1-100. El scheduler intentará distribuir los Pods en nodos distintos, pero si no es posible los programa igualmente. Nótese que la estructura es diferente: cada entrada requiere `weight` y `podAffinityTerm`.

### Campos comunes

- **`labelSelector`**: selecciona Pods con la etiqueta `workload: HighResourceUsage`.
- **`topologyKey: kubernetes.io/hostname`**: la unidad de distribución es el nodo (cada nodo es una "topología" distinta).
