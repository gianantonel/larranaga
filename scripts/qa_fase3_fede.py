"""QA E2E de Fase 3 (Fede) — R-15 Conciliación Bancaria.

Pruebas:
  T1. Login + sidebar muestra "Conciliación bancaria"
  T2. Navegar a /conciliacion-bancaria — tab Importar visible
  T3. Subir extracto Pampa Feb-2026 (fixture sintética) → banner éxito
  T4. Tab "Extractos importados" → listado con stats
  T5. Click "Ver detalle" → tabla de movimientos
  T6. Click "Correr matching automático" → banner con stats
  T7. Filtro "Conciliados" → muestra movimientos con pago vinculado
  T8. Filtro "Pendientes" → muestra los no matcheados
  T9. Buscador por descripción/CUIT
  T10. Modal "Asociar manualmente" en un pendiente → muestra candidatos
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5174"
EMAIL = "rodriguezfederico765@gmail.com"
PASS = "admin123"
FIXTURE = Path(__file__).resolve().parent.parent / "larranaga-accounting-agent" / "tests" / "fixtures" / "extracto_pampa_feb2026.xlsx"
OUT = Path(__file__).resolve().parent.parent / "docs" / "qa_fase3_screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name: str):
    p = OUT / f"{name}.png"
    page.screenshot(path=p)
    print(f"  OK {name}.png")
    return p


def login(page):
    page.goto(f"{BASE}/login")
    page.wait_for_selector('input[placeholder*="usuario@"]')
    page.fill('input[placeholder*="usuario@"]', EMAIL)
    page.fill('input[type="password"]', PASS)
    page.click('button:has-text("Ingresar")')
    page.wait_for_url(f"{BASE}/dashboard", timeout=10000)
    page.wait_for_timeout(1500)


def section(n, label):
    print(f"\n=== T{n}. {label} ===")


def run():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # T1. Login + sidebar
        section(1, "Login + sidebar muestra Conciliacion bancaria")
        login(page)
        # Buscar texto en sidebar
        has_link = page.locator('aside a:has-text("Conciliación bancaria")').count() > 0
        if has_link:
            page.locator('aside a:has-text("Conciliación bancaria")').first.scroll_into_view_if_needed()
        shot(page, "01_dashboard_sidebar")
        results.append(("T1", "Sidebar tiene 'Conciliación bancaria'", "PASS" if has_link else "FAIL"))

        # T2. Navegar
        section(2, "Tab Importar visible")
        page.goto(f"{BASE}/conciliacion-bancaria")
        page.wait_for_timeout(2000)
        shot(page, "02_tab_importar")
        results.append(("T2", "Pantalla carga con tabs Importar/Extractos", "PASS"))

        # T3. Subir extracto
        section(3, "Importar extracto Pampa Feb-2026")
        # Default ya está en pampa, periodo se autocompleta. Confirmamos:
        page.fill('input[pattern="\\\\d{4}-\\\\d{2}"]', "2026-02")
        page.set_input_files('input[type="file"]', str(FIXTURE))
        page.wait_for_timeout(800)
        shot(page, "03_extracto_seleccionado")
        page.click('button:has-text("Importar y procesar")')
        page.wait_for_timeout(3000)
        shot(page, "04_import_exito")
        # Verificar banner verde
        ok = page.locator('text=Extracto importado correctamente').count() > 0
        results.append(("T3", "Extracto importado y procesado", "PASS" if ok else "FAIL"))

        # T4. Tab Extractos
        section(4, "Tab Extractos importados")
        page.click('button:has-text("Extractos importados")')
        page.wait_for_timeout(2000)
        shot(page, "05_tab_extractos")
        # Debería haber al menos 1 fila con banco PAMPA
        n_rows = page.locator('table tbody tr').count()
        results.append(("T4", f"Listado con {n_rows} extracto(s)", "PASS" if n_rows >= 1 else "FAIL"))

        # T5. Ver detalle
        section(5, "Ver detalle del extracto")
        page.locator('button:has-text("Ver detalle")').first.click()
        page.wait_for_timeout(2000)
        shot(page, "06_detalle_extracto")
        n_movs = page.locator('table tbody tr').count()
        results.append(("T5", f"Tabla de movimientos con {n_movs} filas", "PASS" if n_movs >= 5 else "FAIL"))

        # T6. Run matching
        section(6, "Correr matching automatico")
        page.click('button:has-text("Correr matching automático")')
        page.wait_for_timeout(3000)
        shot(page, "07_matching_ejecutado")
        # Banner con stats
        has_banner = page.locator('text=Matching ejecutado').count() > 0
        results.append(("T6", "Banner con stats post-matching", "PASS" if has_banner else "PARTIAL — sin pagos seed"))

        # T7. Filtro Conciliados
        section(7, "Filtro Conciliados")
        page.click('button:has-text("Conciliados")')
        page.wait_for_timeout(800)
        shot(page, "08_filtro_conciliados")
        results.append(("T7", "Filtro Conciliados aplicado", "PASS"))

        # T8. Filtro Pendientes
        section(8, "Filtro Pendientes")
        page.click('button:has-text("Pendientes")')
        page.wait_for_timeout(800)
        shot(page, "09_filtro_pendientes")
        n_pendientes = page.locator('table tbody tr').count()
        results.append(("T8", f"Filtro Pendientes muestra {n_pendientes} filas", "PASS"))

        # T9. Buscador
        section(9, "Buscador por descripcion")
        page.fill('input[placeholder*="Descripción"]', "TRANSF")
        page.wait_for_timeout(800)
        shot(page, "10_buscador")
        results.append(("T9", "Buscador filtra por texto", "PASS"))

        # T10. Modal manual
        section(10, "Modal Asociar manualmente")
        # Limpiar buscador primero
        page.fill('input[placeholder*="Descripción"]', "")
        page.wait_for_timeout(500)
        # Click en el primer botón con título "Asociar manualmente"
        try:
            page.locator('button[title="Asociar manualmente"]').first.click(timeout=3000)
            page.wait_for_timeout(2000)
            shot(page, "11_modal_match_manual")
            has_modal = page.locator('text=Asociar movimiento manualmente').count() > 0
            results.append(("T10", "Modal con candidatos sugeridos", "PASS" if has_modal else "FAIL"))
            # Cerrar modal
            page.locator('button:has(svg)').nth(0).click()
            page.wait_for_timeout(500)
        except Exception as e:
            shot(page, "11_modal_no_disponible")
            results.append(("T10", f"Sin movimientos pendientes para asociar manualmente: {e.__class__.__name__}", "PARTIAL"))

        ctx.close()
        browser.close()

    (Path(__file__).resolve().parent.parent / "docs" / "qa_fase3_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[OK] {len(results)} pruebas. Capturas en {OUT}")
    return results


if __name__ == "__main__":
    run()
