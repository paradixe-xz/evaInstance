#!/usr/bin/env python3
"""
Script para crear archivo Excel de ejemplo con contactos
"""

import pandas as pd

# Datos de ejemplo
contactos = {
    'nombre': [
        'Juan Pérez',
        'María García', 
        'Carlos López',
        'Ana Martínez',
        'Roberto Silva',
        'Laura Rodríguez',
        'Miguel Torres',
        'Carmen Vega',
        'Fernando Ruiz',
        'Patricia Morales'
    ],
    'numero': [
        '+573001234567',
        '3001234568',
        '+573001234569', 
        '3001234570',
        '+573001234571',
        '3001234572',
        '+573001234573',
        '3001234574',
        '+573001234575',
        '3001234576'
    ]
}

# Crear DataFrame
df = pd.DataFrame(contactos)

# Guardar como Excel
df.to_excel('ejemplo_contactos.xlsx', index=False)

print("✅ Archivo Excel creado: ejemplo_contactos.xlsx")
print(f"📊 {len(contactos['nombre'])} contactos de ejemplo")
print("")
print("📋 Contactos incluidos:")
for i, (nombre, numero) in enumerate(zip(contactos['nombre'], contactos['numero']), 1):
    print(f"   {i}. {nombre} - {numero}")
print("")
print("🚀 Para probar el sistema:")
print("   1. Ejecuta: ./run_server.sh")
print("   2. Sube el archivo: ejemplo_contactos.xlsx")
print("   3. Las llamadas se harán automáticamente") 