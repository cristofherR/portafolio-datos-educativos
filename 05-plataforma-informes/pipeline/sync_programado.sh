#!/usr/bin/env bash
# Sincroniza la plataforma AJ (TOV -> informes -> web).
# Silencioso si no hay nada que reportar: imprime NO_REPLY.
# Uso: sync_programado.sh
set -uo pipefail
cd "$(dirname "$0")/.." || { echo "no se pudo entrar al proyecto"; exit 0; }

HORA="$(TZ=America/Lima date '+%d/%m %H:%M')"

correr() { python3 pipeline/actualizar.py "$@" 2>&1; }

SALIDA="$(correr)"
RC=$?
AVISO_BD=""
# Si falla leyendo la base (red/credenciales), se actualiza igual con lo ultimo consolidado.
if [ $RC -ne 0 ] && printf '%s' "$SALIDA" | grep -q "1/4 Consolidar datos"; then
  SALIDA="$(correr --sin-bd)"
  RC=$?
  AVISO_BD=" (no se pudo leer la base: se usó la última consolidación)"
fi

LINEA="$(printf '%s\n' "$SALIDA" | grep -m1 '^INFORMES ->')"
RESUMEN="$(printf '%s\n' "$SALIDA" | grep -m1 '^RESULTADO:')"

# --- fallo real: se reporta ---
if [ $RC -ne 0 ] || [ -z "$RESUMEN" ]; then
  printf 'Aviso plataforma AJ (%s): no se pudo completar la actualización.%s\n' "$HORA" "$AVISO_BD"
  printf '%s\n' "$SALIDA" | tail -8
  exit 0
fi

num() { printf '%s' "$LINEA" | sed -n "s/.*| $1 \([0-9][0-9]*\).*/\1/p"; }
NUEVOS="$(num nuevos)"; ACT="$(num actualizados)"; OBS="$(num obsoletos)"; ERR="$(num errores)"
FALTAN="$(printf '%s' "$RESUMEN" | sed -n 's/.*PDF faltantes \([0-9][0-9]*\).*/\1/p')"
: "${NUEVOS:=0}" "${ACT:=0}" "${OBS:=0}" "${ERR:=0}" "${FALTAN:=0}"

# --- nada cambio: silencio total ---
if [ "$NUEVOS" = 0 ] && [ "$ACT" = 0 ] && [ "$OBS" = 0 ] && [ "$ERR" = 0 ] && [ "$FALTAN" = 0 ]; then
  echo NO_REPLY
  exit 0
fi

printf 'Plataforma AJ actualizada (%s)%s\n' "$HORA" "$AVISO_BD"
printf 'Informes nuevos: %s | actualizados: %s | retirados: %s | con error: %s\n' "$NUEVOS" "$ACT" "$OBS" "$ERR"
printf '%s\n' "$RESUMEN"
if [ -n "${AJ_URL:-}" ]; then printf '%s\n' "$AJ_URL"; fi
