#!/bin/bash
# Pre-commit reminder: Asegurar que actualizaciones-larranaga.md fue actualizado

echo ""
echo "======================================"
echo "⚠️  PRE-COMMIT REMINDER"
echo "======================================"
echo ""
echo "❓ ¿Actualizaste actualizaciones-larranaga.md?"
echo ""
echo "📋 Checklist:"
echo "  [ ] ¿Leíste actualizaciones-larranaga.md?"
echo "  [ ] ¿Documentaste QUÉ cambiste?"
echo "  [ ] ¿Documentaste DÓNDE cambiste?"
echo "  [ ] ¿Incluiste el commit hash?"
echo ""
echo "📖 Guías:"
echo "  - docs/CONTRIBUTING.md: Instrucciones detalladas"
echo "  - docs/PLANTILLA-CAMBIOS.txt: Template para copiar"
echo "  - docs/README_POLITICAS.md: Políticas del proyecto"
echo ""
echo "======================================"
echo ""

# Verificar si actualizaciones-larranaga.md fue modificado
if ! git diff --cached --name-only | grep -q "docs/actualizaciones-larranaga.md"; then
  echo "⚠️  ADVERTENCIA: docs/actualizaciones-larranaga.md no está en el staging area"
  echo ""
  echo "Si hiciste cambios importantes, deberías actualizar el documento."
  echo "Lee docs/CONTRIBUTING.md para más detalles."
  echo ""
fi

exit 0
