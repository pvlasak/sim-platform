#!/bin/bash
kubectl apply -f cluster_autoscaler_autodiscover.yaml
kubectl apply -f mongodb-storageClass.yaml
helm repo add bitnami https://charts.bitnami.com/bitnami
helm search repo bitnami
helm install mongodb --values mongodb-helm-values.yaml bitnami/mongodb
kubectl apply -f mongodb-configmap.yaml
kubectl apply -f backend-configmap.yaml
kubectl apply -f gitlab-private-key-secret.yaml
kubectl apply -f known_hosts_config.yaml
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
kubectl create namespace ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx
kubectl apply -f api-ingress.yaml
kubectl apply -f frontend-ingress.yaml
