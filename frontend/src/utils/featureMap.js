// Mapeo R-XX → metadata estática. Sincronizar con backend/app/mock_data.py:CATALOGO_REQUISITOS.

export const FEATURE_MAP = [
  // Fase 1
  { codigo: 'R-01', fase: 1, area: 'IVA', ruta: '/herramientas' },
  { codigo: 'R-02', fase: 1, area: 'IVA', ruta: '/herramientas' },
  { codigo: 'R-03', fase: 1, area: 'ADM', ruta: '/honorarios' },
  { codigo: 'R-04', fase: 1, area: 'ADM', ruta: '/liquidaciones' },
  { codigo: 'R-05', fase: 1, area: 'IVA', ruta: '/retenciones' },
  { codigo: 'R-07', fase: 1, area: 'ADM', ruta: '/cuentas-corrientes' },
  // Fase 2
  { codigo: 'R-06', fase: 2, area: 'IVA', ruta: '/iva' },
  { codigo: 'R-08', fase: 2, area: 'ADM', ruta: '/cobros' },
  { codigo: 'R-09', fase: 2, area: 'IVA', ruta: '/maestro-proveedores' },
  { codigo: 'R-10', fase: 2, area: 'IVA', ruta: null },
  { codigo: 'R-14', fase: 2, area: 'ADM', ruta: null },
  // Fase 3
  { codigo: 'R-11', fase: 3, area: 'ADM', ruta: '/flujo-fondos' },
  { codigo: 'R-12', fase: 3, area: 'ADM', ruta: '/retiros' },
  { codigo: 'R-13', fase: 3, area: 'ADM', ruta: '/actualizar-honorarios' },
  { codigo: 'R-15', fase: 3, area: 'IVA+ADM', ruta: '/conciliacion-bancaria' },
  // Fase 4
  { codigo: 'R-16', fase: 4, area: 'IVA' },
  { codigo: 'R-17', fase: 4, area: 'ADM' },
  { codigo: 'R-18', fase: 4, area: 'IVA' },
  { codigo: 'R-19', fase: 4, area: 'IVA' },
  { codigo: 'R-20', fase: 4, area: 'IVA+ADM' },
]
