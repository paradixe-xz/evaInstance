# Eva Dashboard - Design System
*Inspirado en Fynix Financial Dashboard*

## 🎨 Paleta de Colores

### Colores Primarios
- **Verde Principal**: `#86efac` / `#4ade80` (Lime/Green 300-400)
  - Uso: CTAs principales, elementos destacados, gráficos positivos
- **Verde Oscuro**: `#16a34a` (Green 600)
  - Uso: Hover states, elementos secundarios

### Colores Neutrales
- **Fondo Principal**: `#fafafa` / `#f5f5f5` (Gray 50)
- **Fondo Tarjetas**: `#ffffff` (White)
- **Texto Principal**: `#0f172a` / `#1e293b` (Slate 900/800)
- **Texto Secundario**: `#64748b` (Slate 500)
- **Bordes**: `#e2e8f0` (Slate 200)

### Colores de Estado
- **Éxito**: `#22c55e` (Green 500)
- **Error/Negativo**: `#ef4444` (Red 500)
- **Advertencia**: `#f59e0b` (Amber 500)
- **Info**: `#3b82f6` (Blue 500)

### Colores de Gráficos
- **Serie 1 (Primaria)**: `#86efac` (Verde claro)
- **Serie 2 (Secundaria)**: `#1e293b` (Slate oscuro)
- **Fondo gráficos**: Transparente o blanco

---

## 📝 Tipografía

### Familia de Fuentes
- **Principal**: Inter, system-ui, sans-serif
- **Monoespaciada**: 'Geist Mono' (para números/datos)

### Escala Tipográfica
\`\`\`
Heading 1: 32px / 2rem - font-bold - tracking-tight
Heading 2: 24px / 1.5rem - font-semibold
Heading 3: 20px / 1.25rem - font-semibold
Body Large: 16px / 1rem - font-normal
Body: 14px / 0.875rem - font-normal
Small: 12px / 0.75rem - font-normal
Tiny: 11px / 0.6875rem - font-medium
\`\`\`

### Números/Métricas
- **Grandes (Balance)**: 36-48px, font-bold, tabular-nums
- **Medianos (KPIs)**: 24-32px, font-semibold, tabular-nums
- **Pequeños (Tablas)**: 14px, font-medium, tabular-nums

---

## 📏 Espaciado

### Sistema de Espaciado (múltiplos de 4px)
\`\`\`
xs: 4px   (0.25rem)
sm: 8px   (0.5rem)
md: 16px  (1rem)
lg: 24px  (1.5rem)
xl: 32px  (2rem)
2xl: 48px (3rem)
3xl: 64px (4rem)
\`\`\`

### Espaciado de Componentes
- **Padding Tarjetas**: 24px (lg)
- **Gap entre Tarjetas**: 24px (lg)
- **Padding Sidebar**: 16px (md)
- **Margin entre Secciones**: 32px (xl)

---

## 🎯 Componentes

### Tarjetas (Cards)
\`\`\`
- Fondo: Blanco (#ffffff)
- Border radius: 16px (rounded-2xl)
- Sombra: Sutil (shadow-sm)
- Padding: 24px
- Border: Ninguno o 1px #e2e8f0
\`\`\`

### Botones

**Primario (CTA)**
\`\`\`
- Fondo: Verde (#4ade80)
- Texto: Slate oscuro (#1e293b)
- Padding: 12px 24px
- Border radius: 12px (rounded-xl)
- Font: 14px, font-medium
- Hover: Verde más oscuro (#22c55e)
\`\`\`

**Secundario**
\`\`\`
- Fondo: Transparente o Slate 100
- Texto: Slate 700
- Border: 1px Slate 300
- Padding: 12px 24px
- Border radius: 12px
\`\`\`

**Icono**
\`\`\`
- Tamaño: 40px × 40px
- Border radius: 10px (rounded-lg)
- Hover: Fondo Slate 100
\`\`\`

### Inputs
\`\`\`
- Altura: 44px
- Padding: 12px 16px
- Border: 1px #e2e8f0
- Border radius: 12px (rounded-xl)
- Focus: Border verde + ring verde sutil
- Placeholder: Slate 400
\`\`\`

### Sidebar
\`\`\`
- Ancho: 240px
- Fondo: Blanco o Gray 50
- Padding: 16px
- Items altura: 40px
- Border radius items: 10px
- Hover: Fondo Slate 100
- Activo: Fondo verde claro + texto verde oscuro
\`\`\`

---

## 📊 Gráficos y Visualizaciones

### Estilo General
- **Colores**: Verde claro + Slate oscuro
- **Grid**: Líneas sutiles (#e2e8f0)
- **Ejes**: Texto pequeño (12px), Slate 500
- **Tooltips**: Fondo blanco, sombra, border radius 8px

### Gráficos de Barras
- **Ancho barras**: Proporcional, gap 8px
- **Border radius**: 4px en la parte superior
- **Apiladas**: Verde claro (positivo) + Slate oscuro (negativo)

### Gráficos Circulares (Donut)
- **Grosor**: 20-24px
- **Colores**: Verde (principal) + Slate (secundario)
- **Centro**: Valor grande + label pequeño

---

## 🎭 Efectos y Animaciones

### Sombras
\`\`\`
Sutil: shadow-sm (0 1px 2px rgba(0,0,0,0.05))
Media: shadow-md (0 4px 6px rgba(0,0,0,0.07))
Elevada: shadow-lg (0 10px 15px rgba(0,0,0,0.1))
\`\`\`

### Transiciones
\`\`\`
Estándar: transition-all duration-200 ease-in-out
Hover: scale-[1.02] o brightness-95
\`\`\`

### Border Radius
\`\`\`
Pequeño: 8px (rounded-lg)
Medio: 12px (rounded-xl)
Grande: 16px (rounded-2xl)
Completo: 9999px (rounded-full)
\`\`\`

---

## 📱 Layout y Grid

### Estructura Principal
\`\`\`
- Sidebar: 240px fijo (izquierda)
- Contenido: flex-1 con max-width
- Padding contenido: 32px
- Gap entre columnas: 24px
\`\`\`

### Grid de Tarjetas
\`\`\`
- Desktop: grid-cols-3 o grid-cols-2
- Tablet: grid-cols-2
- Mobile: grid-cols-1
- Gap: 24px
\`\`\`

### Responsive Breakpoints
\`\`\`
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
\`\`\`

---

## ✨ Principios de Diseño

1. **Minimalismo**: Mucho espacio en blanco, sin elementos decorativos innecesarios
2. **Jerarquía Clara**: Tamaños de texto y peso visual bien definidos
3. **Consistencia**: Mismo border radius, espaciado y colores en todo el sistema
4. **Legibilidad**: Alto contraste para texto, números grandes para métricas importantes
5. **Accesibilidad**: Contraste WCAG AA mínimo, tamaños táctiles de 44px
6. **Datos Primero**: Las visualizaciones y números son el foco principal
7. **Verde como Acento**: No abusar del verde, usarlo estratégicamente para CTAs y datos positivos

---

## 🎨 Ejemplos de Uso

### Tarjeta de Métrica Principal
- Fondo: Verde con gradiente sutil
- Número grande: 48px, bold, blanco
- Label: 14px, verde oscuro
- Botones: Contraste alto (uno verde oscuro, uno blanco)

### Tarjeta de Métrica Secundaria
- Fondo: Blanco
- Icono: 24px, color según categoría
- Número: 32px, semibold, slate 900
- Label: 12px, slate 500
- Cambio porcentual: 14px, verde o rojo según valor

### Tabla de Transacciones
- Headers: 12px, uppercase, slate 500, font-medium
- Rows: 14px, slate 700, altura 56px
- Hover: Fondo slate 50
- Bordes: Sutiles, slate 200
- Estados: Pills con colores (verde/rojo/amarillo)

---

## 🚀 Implementación con Tailwind

### Configuración de Colores
\`\`\`js
colors: {
  primary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
  }
}
\`\`\`

### Clases Comunes
\`\`\`
Card: bg-white rounded-2xl shadow-sm p-6
Button Primary: bg-green-400 text-slate-900 rounded-xl px-6 py-3 font-medium hover:bg-green-500
Button Secondary: bg-slate-100 text-slate-700 rounded-xl px-6 py-3 font-medium hover:bg-slate-200
Input: border border-slate-200 rounded-xl px-4 py-3 focus:border-green-400 focus:ring-2 focus:ring-green-100
\`\`\`

---

**Última actualización**: 2025-01-18
**Versión**: 1.0
