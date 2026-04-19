# TokenGuard — Kit de Ahorro de Tokens para Claude Code

## Reglas

### 1. VERIFICA ANTES
Antes de implementar nada, comprueba el código existente con grep/read. Nunca asumas que algo no existe. Una búsqueda de 100 tokens evita una reimplementación de 70.000.

### 2. GREP > AGENTE
Usa Grep o Read directamente (~100 tokens) en lugar de lanzar subagentes de exploración (~40.000 tokens). Busca primero, explora solo si la búsqueda falla.

### 3. UNO A LA VEZ
Construye un módulo, pruébalo, verifica que funciona. Nunca acumules varios cambios sin probar. Cada suposición no verificada se convierte en un rollback caro.

### 4. SOLO LO QUE SE PIDE
Haz exactamente lo que se solicitó. Arreglar un bug no es una invitación a refactorizar tres archivos. Una función simple no necesita configurabilidad extra ni cambios en la documentación.

## Informe de Eficiencia

Comprueba cuántos tokens desperdicia tu agente en lecturas duplicadas y operaciones innecesarias. Ejecuta desde el directorio TokenGuard:

```
python informe.py
```

Abre un dashboard HTML con tus métricas reales — sesiones analizadas, ratio de eficiencia, tokens desperdiciados, archivos más releídos. Cero tokens consumidos (solo lee logs locales).

Ejecútalo cada 5-10 sesiones para ver tu progreso.
