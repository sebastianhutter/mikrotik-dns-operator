{{/*
Expand the name of the chart.
*/}}
{{- define "mikrotik-dns-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mikrotik-dns-operator.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mikrotik-dns-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mikrotik-dns-operator.labels" -}}
helm.sh/chart: {{ include "mikrotik-dns-operator.chart" . }}
{{ include "mikrotik-dns-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mikrotik-dns-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mikrotik-dns-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mikrotik-dns-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mikrotik-dns-operator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the configmap and secret to use
*/}}
{{- define "mikrotik-dns-operator.configMapName" -}}
{{- include "mikrotik-dns-operator.fullname" . }}
{{- end }}

{{- define "mikrotik-dns-operator.secretName" -}}
{{- if empty .Values.mikrotik.secretName }}
{{- include "mikrotik-dns-operator.fullname" . }}
{{- else }}
{{- .Values.mikrotik.secretName}}
{{- end }}
{{- end }}