#!/bin/bash
# Pipeline de seguridad - Avance 2 - Tema 4: Foro y reseñas
# Consolida 3 controles en UN SOLO veredicto: BLOQUEA o PERMITE

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p reportes

FALLOS=0
RESUMEN=""

echo "=================================================="
echo " PIPELINE DE SEGURIDAD - avance2_HTI"
echo " Fecha: $(date)"
echo "=================================================="

# --- Etapa 1: Escaneo de secretos (gitleaks) ---
echo ""
echo "--- Etapa 1: Escaneo de secretos (gitleaks) ---"
echo "Umbral: bloquea si se detecta CUALQUIER secreto."
gitleaks detect --source . --no-git -v
if [ $? -ne 0 ]; then
  echo "[FALLA] Se detectaron secretos expuestos en el codigo."
  FALLOS=$((FALLOS+1))
  RESUMEN="$RESUMEN\n- Secretos expuestos (gitleaks)"
else
  echo "[OK] No se detectaron secretos."
fi

# --- Etapa 2: Dependencias vulnerables (pip-audit) ---
echo ""
echo "--- Etapa 2: Dependencias vulnerables (pip-audit) ---"
echo "Umbral: bloquea si se encuentra cualquier CVE conocido."
API_RESULT=0
MOD_RESULT=0
pip-audit -r app/api/requirements.txt
API_RESULT=$?
pip-audit -r app/moderador/requirements.txt
MOD_RESULT=$?

if [ $API_RESULT -ne 0 ] || [ $MOD_RESULT -ne 0 ]; then
  echo "[FALLA] Se encontraron vulnerabilidades conocidas en dependencias."
  FALLOS=$((FALLOS+1))
  RESUMEN="$RESUMEN\n- Dependencias vulnerables (pip-audit)"
else
  echo "[OK] Sin vulnerabilidades conocidas en dependencias."
fi

# --- Etapa 3: Dockerfile endurecido (hadolint) ---
echo ""
echo "--- Etapa 3: Lint de Dockerfile (hadolint) ---"
echo "Umbral: bloquea con hallazgos de nivel error."
DOCKER_ERRORS=0
for df in app/api/Dockerfile app/moderador/Dockerfile; do
  echo "Revisando $df"
  hadolint "$df" --failure-threshold error
  if [ $? -ne 0 ]; then
    DOCKER_ERRORS=$((DOCKER_ERRORS+1))
  fi
done

if [ $DOCKER_ERRORS -gt 0 ]; then
  echo "[FALLA] $DOCKER_ERRORS Dockerfile(s) con errores de buenas practicas."
  FALLOS=$((FALLOS+1))
  RESUMEN="$RESUMEN\n- Dockerfile con errores (hadolint)"
else
  echo "[OK] Dockerfiles cumplen buenas practicas minimas."
fi

# --- Veredicto final ---
echo ""
echo "=================================================="
if [ $FALLOS -gt 0 ]; then
  echo " VEREDICTO FINAL: BLOQUEADO"
  echo " Etapas con hallazgos: $FALLOS"
  echo -e "$RESUMEN"
  echo "=================================================="
  exit 1
else
  echo " VEREDICTO FINAL: PERMITIDO"
  echo " Todas las etapas pasaron sus umbrales."
  echo "=================================================="
  exit 0
fi
