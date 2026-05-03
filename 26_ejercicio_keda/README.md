# Ejercicio KEDA — Escalado basado en cola MySQL

Demuestra cómo KEDA escala un Deployment en función del número de filas en una tabla MySQL.

## Arquitectura

```
[Producer] → INSERT jobs → [MySQL: tabla jobs] ← SELECT/DELETE ← [Consumer x N]
                                    ↑
                               [KEDA ScaledObject]
                         (1 réplica por cada 3 filas)
```

- **Producer**: inserta 1 job por segundo.
- **Consumer**: procesa (borra) 1 job cada 5 segundos. Cada réplica consume 0.2 jobs/s.
- **KEDA**: escala el consumer entre 0 y 10 réplicas según `COUNT(*) FROM jobs`.

## Prerrequisitos

### 1. Instalar KEDA

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

### 2. Verificar que KEDA está listo

```bash
kubectl get pods -n keda
```

## Despliegue

```bash
# 1. MySQL
kubectl apply -f mysql.yaml

# 2. Esperar a que MySQL esté listo
kubectl wait --for=condition=ready pod -l app=mysql --timeout=60s

# 3. KEDA: Secret + TriggerAuthentication + ScaledObject
kubectl apply -f keda.yaml

# 4. Consumer (KEDA lo gestionará, arrancará con 0 réplicas)
kubectl apply -f consumer.yaml

# 5. Producer (empieza a insertar jobs)
kubectl apply -f producer.yaml
```

## Observar el escalado

En una terminal, observar el ScaledObject y las réplicas del consumer en tiempo real:

```bash
watch -n 2 'echo "=== Jobs en cola ===" && kubectl exec deploy/mysql -- mysql -uroot -pcursok8s -e "SELECT COUNT(*) FROM cursodb.jobs" 2>/dev/null && echo "=== Réplicas consumer ===" && kubectl get deployment consumer'
```

En otra terminal, ver los logs del consumer:

```bash
kubectl logs -l app=consumer -f --max-log-requests 10
```

## Dinámica esperada

| Tiempo | Jobs en cola | Réplicas consumer |
|--------|-------------|-------------------|
| 0-15s  | 0-15        | 0 → 1             |
| 15-30s | 15-30       | 1 → 5             |
| ~60s   | estabiliza  | ~5                |

Con 5 réplicas el sistema se equilibra: el producer inserta 1/s y los 5 consumers procesan 5×0.2 = 1/s.

## Detener el producer y observar el escalado a la baja

```bash
kubectl delete -f producer.yaml
```

KEDA esperará el `cooldownPeriod` (30s) tras vaciar la cola y escalará el consumer a 0 réplicas.

## Limpiar

```bash
kubectl delete -f producer.yaml -f consumer.yaml -f keda.yaml -f mysql.yaml
```

## Build de imágenes (referencia)

```bash
docker build -t jvelascoiti/keda-producer:latest producer/
docker build -t jvelascoiti/keda-consumer:latest consumer/
docker push jvelascoiti/keda-producer:latest
docker push jvelascoiti/keda-consumer:latest
```
