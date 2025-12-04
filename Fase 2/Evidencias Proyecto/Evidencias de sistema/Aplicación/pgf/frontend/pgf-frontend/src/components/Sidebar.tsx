/**
 * Componente Sidebar - Menú de navegación lateral.
 * 
 * Este componente proporciona la navegación principal de la aplicación,
 * mostrando diferentes opciones según los permisos del usuario.
 * 
 * Características:
 * - Menú colapsable (se puede expandir/contraer)
 * - Filtrado por roles y permisos
 * - Resaltado de ruta activa
 * - Diseño responsive con soporte dark mode
 * - Colores PepsiCo (#003DA5) para elementos activos
 * 
 * Dependencias:
 * - next/link: Para navegación
 * - next/navigation: usePathname para detectar ruta actual
 * - @heroicons/react: Iconos
 * - @/store/auth: useAuth para permisos
 * 
 * Relaciones:
 * - Usado en: layout.tsx (layout principal)
 * - Depende de: useAuth store para verificar permisos
 * - Complementa: Topbar.tsx (barra superior)
 */

"use client";  // Componente de cliente (usa hooks)

import Link from "next/link";  // Componente de Next.js para navegación
import { usePathname } from "next/navigation";  // Hook para obtener ruta actual
import { useState, useEffect } from "react";  // Hooks de React
import { useAuth } from "@/store/auth";  // Store de autenticación
import {
  HomeIcon,        // Icono de dashboard
  UserIcon,        // Icono de usuarios
  WrenchIcon,      // Icono de órdenes de trabajo
  TruckIcon,       // Icono de vehículos
  Bars3Icon,       // Icono de menú hamburguesa
  UserGroupIcon,   // Icono de choferes
  CalendarIcon,    // Icono de agenda
  PhotoIcon,       // Icono de evidencias/fotos
  CheckCircleIcon, // Icono de check/QA
  ChartBarIcon,    // Icono de gráficos/analizador
  CogIcon,         // Icono de configuración
  ShieldCheckIcon, // Icono de auditoría/seguridad
  DocumentTextIcon, // Icono de reportes
  ClipboardDocumentListIcon, // Icono de historial
  CubeIcon,        // Icono de repuestos/inventario
  ArchiveBoxIcon,  // Icono de stock
  ClipboardDocumentCheckIcon, // Icono de solicitudes
  ArrowsRightLeftIcon, // Icono de movimientos
} from "@heroicons/react/24/outline";  // Iconos outline de Heroicons
import PepsiCoLogo from "@/components/PepsiCoLogo";

/**
 * Componente Sidebar.
 * 
 * Renderiza el menú lateral de navegación con:
 * - Logo/título de la aplicación
 * - Botón para colapsar/expandir
 * - Lista de items de menú filtrados por permisos
 * 
 * Estados:
 * - open: Indica si el sidebar está expandido (true) o colapsado (false)
 */
export default function Sidebar() {
  // Estado: sidebar expandido o colapsado
  const [open, setOpen] = useState(true);
  
  // Ruta actual (para resaltar item activo)
  const pathname = usePathname();
  
  // Obtener usuario y función de verificación de permisos
  const { user, allowed } = useAuth();

  /**
   * Menú organizado por secciones para mejor UX.
   * 
   * Estructura:
   * - section: Nombre de la sección (para agrupar)
   * - items: Array de items de menú en esa sección
   * 
   * Cada item tiene:
   * - href: Ruta a la que navega
   * - label: Texto visible
   * - icon: Componente de icono
   * - section: Sección para verificar permisos (usado con allowed())
   * - roles: Roles específicos que pueden ver este item (opcional)
   */
  const menuSections = [
    {
      title: "Dashboards",
      items: [
        {
          href: "/dashboard/ejecutivo",
          label: "Dashboard Ejecutivo",
          icon: HomeIcon,
          section: "reports",
          roles: ["EJECUTIVO", "ADMIN", "SPONSOR"]
        },
        {
          href: "/supervisor/dashboard",
          label: "Dashboard Zona",
          icon: HomeIcon,
          section: "reports",
          roles: ["SUPERVISOR", "ADMIN"]
        },
        {
          href: "/jefe-taller/dashboard",
          label: "Dashboard Taller",
          icon: HomeIcon,
          section: "workorders",
          roles: ["JEFE_TALLER", "ADMIN"]
        },
        {
          href: "/subgerente/dashboard",
          label: "Dashboard Nacional",
          icon: HomeIcon,
          section: "reports",
          roles: ["SUBGERENTE_NACIONAL", "ADMIN"]
        },
        {
          href: "/coordinador/dashboard",
          label: "Dashboard Coordinador",
          icon: HomeIcon,
          section: "reports",
          roles: ["COORDINADOR_ZONA", "ADMIN"]
        },
      ]
    },
    {
      title: "Vehículos",
      items: [
        {
          href: "/vehicles",
          label: "Listado de Vehículos",
          icon: TruckIcon,
          section: "vehicles",
          roles: ["ADMIN", "SUPERVISOR", "MECANICO", "GUARDIA", "JEFE_TALLER", "COORDINADOR_ZONA", "SPONSOR", "CHOFER", "EJECUTIVO"]
        },
        {
          href: "/vehicles/ingreso",
          label: "Registrar Ingreso",
          icon: TruckIcon,
          section: "vehicles",
          roles: ["GUARDIA", "ADMIN", "JEFE_TALLER"]
        },
        {
          href: "/vehicles/salida",
          label: "Registrar Salida",
          icon: TruckIcon,
          section: "vehicles",
          roles: ["GUARDIA", "ADMIN", "JEFE_TALLER"]
        },
        {
          href: "/vehicles/ingresos-hoy",
          label: "Ingresos del Día",
          icon: ClipboardDocumentListIcon,
          section: "vehicles",
          roles: ["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]
        },
        {
          href: "/vehicles/ingresos-historial",
          label: "Historial de Ingresos",
          icon: ClipboardDocumentListIcon,
          section: "vehicles",
          roles: ["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]
        },
        {
          href: "/chofer",
          label: "Mi Vehículo",
          icon: UserIcon,
          section: "vehicles",
          roles: ["CHOFER"]
        },
      ]
    },
    {
      title: "Órdenes de Trabajo",
      items: [
        {
          href: "/workorders",
          label: "Todas las OTs",
          icon: WrenchIcon,
          section: "workorders",
          roles: ["ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA", "EJECUTIVO", "ADMINISTRATIVO_TALLER", "BODEGA"]
        },
        {
          href: "/workorders/create",
          label: "Crear OT",
          icon: WrenchIcon,
          section: "workorders",
          roles: ["JEFE_TALLER", "ADMIN"]
        },
        {
          href: "/mecanico",
          label: "Mis OTs",
          icon: WrenchIcon,
          section: "workorders",
          roles: ["MECANICO"]
        },
        {
          href: "/jefe-taller/gestor",
          label: "Gestor de OTs",
          icon: WrenchIcon,
          section: "workorders",
          roles: ["JEFE_TALLER", "ADMIN"]
        },
        {
          href: "/jefe-taller/asignacion",
          label: "Asignar Mecánicos",
          icon: UserGroupIcon,
          section: "workorders",
          roles: ["JEFE_TALLER", "ADMIN"]
        },
        {
          href: "/jefe-taller/qa",
          label: "Control de Calidad",
          icon: CheckCircleIcon,
          section: "workorders",
          roles: ["JEFE_TALLER", "ADMIN"]
        },
        {
          href: "/supervisor/analizador",
          label: "Analizador de OTs",
          icon: ChartBarIcon,
          section: "workorders",
          roles: ["SUPERVISOR", "ADMIN"]
        },
      ]
    },
    {
      title: "Personas",
      items: [
        {
          href: "/users",
          label: "Usuarios",
          icon: UserIcon,
          section: "users",
          roles: ["ADMIN", "SUPERVISOR"]
        },
        {
          href: "/drivers",
          label: "Choferes",
          icon: UserGroupIcon,
          section: "drivers",
          roles: ["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]
        },
        {
          href: "/drivers/asignacion",
          label: "Asignar Vehículos",
          icon: TruckIcon,
          section: "drivers",
          roles: ["ADMIN"]
        },
      ]
    },
    {
      title: "Inventario y Bodega",
      items: [
        {
          href: "/inventory/repuestos",
          label: "Repuestos",
          icon: CubeIcon,
          section: "inventory",
          roles: ["BODEGA", "ADMIN", "JEFE_TALLER", "SUPERVISOR"]
        },
        {
          href: "/inventory/stock",
          label: "Control de Stock",
          icon: ArchiveBoxIcon,
          section: "inventory",
          roles: ["BODEGA", "ADMIN"]
        },
        {
          href: "/inventory/solicitudes",
          label: "Solicitudes",
          icon: ClipboardDocumentCheckIcon,
          section: "inventory",
          roles: ["BODEGA", "ADMIN", "JEFE_TALLER", "SUPERVISOR", "MECANICO"]
        },
        {
          href: "/inventory/movimientos",
          label: "Movimientos",
          icon: ArrowsRightLeftIcon,
          section: "inventory",
          roles: ["BODEGA", "ADMIN"]
        },
      ]
    },
    {
      title: "Recursos y Documentos",
      items: [
        {
          href: "/evidences",
          label: "Evidencias",
          icon: PhotoIcon,
          section: "evidences",
          roles: ["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER"]
        },
        {
          href: "/scheduling",
          label: "Agenda",
          icon: CalendarIcon,
          section: "scheduling",
          roles: ["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]
        },
      ]
    },
    {
      title: "Reportes y Auditoría",
      items: [
        {
          href: "/reports",
          label: "Reportes",
          icon: DocumentTextIcon,
          section: "reports",
          roles: ["ADMIN", "SPONSOR", "EJECUTIVO", "SUBGERENTE_NACIONAL"]
        },
        {
          href: "/auditor/dashboard",
          label: "Auditoría Sistema",
          icon: ShieldCheckIcon,
          section: "reports",
          roles: ["ADMIN", "AUDITOR_INTERNO"]
        },
        {
          href: "/subgerente/auditoria",
          label: "Auditoría Vehículos",
          icon: ShieldCheckIcon,
          section: "vehicles",
          roles: ["SUBGERENTE_NACIONAL", "ADMIN"]
        },
      ]
    },
    {
      title: "Administración",
      items: [
        {
          href: "/admin/configuracion",
          label: "Configuración",
          icon: CogIcon,
          section: "users",
          roles: ["ADMIN"]
        },
        {
          href: "/admin/integraciones",
          label: "Integraciones",
          icon: CogIcon,
          section: "users",
          roles: ["ADMIN"]
        },
        {
          href: "/coordinador",
          label: "Panel Coordinador",
          icon: UserIcon,
          section: "vehicles",
          roles: ["COORDINADOR_ZONA", "ADMIN"]
        },
      ]
    },
  ];

  /**
   * Aplanar todas las secciones en un solo array para filtrar.
   */
  const allMenuItems = menuSections.flatMap(section => section.items);

  /**
   * Filtrar menú según permisos del usuario y agrupar por secciones.
   * 
   * Lógica:
   * 1. Si el item tiene roles específicos:
   *    - Verificar que el usuario tenga uno de esos roles
   * 2. Si no tiene roles:
   *    - Verificar permisos con allowed(section)
   * 
   * Esto asegura que cada usuario solo vea las opciones
   * a las que tiene acceso.
   */
  const filteredSections = menuSections.map(section => ({
    ...section,
    items: section.items.filter((item) => {
      // Si tiene roles específicos, verificar que el usuario tenga uno
      if (item.roles && user) {
        return item.roles.includes(user.rol as any);
      }
      // Si no tiene roles, verificar con allowed()
      return !item.section || allowed(item.section);
    })
  })).filter(section => section.items.length > 0); // Solo mostrar secciones con items

  /**
   * Render del sidebar.
   * 
   * Estructura:
   * - Header con logo PepsiCo y botón de colapsar
   * - Nav con secciones agrupadas y items de menú
   * 
   * Clases CSS:
   * - w-64: Ancho expandido (256px)
   * - w-20: Ancho colapsado (80px)
   * - fixed: Posición fija en la izquierda
   * - z-30: Z-index para estar sobre otros elementos
   */
  return (
    <aside
      className={`h-screen bg-gradient-to-b from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 shadow-xl 
      transition-all duration-300 border-r-2 border-[#003DA5]/20 dark:border-[#003DA5]/30
      ${open ? "w-64" : "w-20"} fixed left-0 top-0 z-30 flex flex-col`}
    >
      {/* Header con logo y botón de colapsar */}
      <div className="flex items-center justify-between p-4 border-b-2 border-[#003DA5]/20 dark:border-[#003DA5]/30 bg-gradient-to-r from-[#003DA5]/5 to-transparent flex-shrink-0">
        {open ? (
          <div className="flex items-center gap-2">
            <PepsiCoLogo size="sm" variant="default" showText={true} text="PGF" />
          </div>
        ) : (
          <PepsiCoLogo size="sm" variant="default" />
        )}
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-lg hover:bg-[#003DA5]/10 dark:hover:bg-[#003DA5]/20 transition-colors"
          aria-label={open ? "Colapsar menú" : "Expandir menú"}
        >
          <Bars3Icon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        </button>
      </div>

      {/* Navegación con secciones - Área con scroll */}
      <nav className="flex-1 overflow-y-auto mt-4 pb-4">
        {filteredSections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-6">
            {/* Título de sección (solo visible si está expandido) */}
            {open && (
              <div className="px-4 py-2 mb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {section.title}
                </h3>
              </div>
            )}
            
            {/* Items de la sección */}
            <div className="space-y-1">
              {section.items.map((m) => {
                // Verificar si esta ruta está activa
                const isActive = pathname === m.href || pathname?.startsWith(m.href + "/");
                
                return (
                  <Link
                    key={m.href}
                    href={m.href}
                    className={`flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg
                    transition-all duration-200 group relative
                    ${
                      isActive
                        ? "bg-[#003DA5] text-white shadow-md shadow-[#003DA5]/30"
                        : "hover:bg-[#003DA5]/10 dark:hover:bg-[#003DA5]/20 text-gray-700 dark:text-gray-200"
                    }`}
                  >
                    {/* Indicador lateral para item activo */}
                    {isActive && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-white rounded-r-full"></div>
                    )}
                    
                    {/* Icono del item */}
                    <m.icon 
                      className={`w-5 h-5 flex-shrink-0 ${
                        isActive 
                          ? "text-white" 
                          : "text-gray-600 dark:text-gray-400 group-hover:text-[#003DA5] dark:group-hover:text-[#00B4E6]"
                      }`} 
                    />
                    
                    {/* Label solo visible si está expandido */}
                    {open && (
                      <span className={`font-medium text-sm ${
                        isActive 
                          ? "text-white" 
                          : "text-gray-700 dark:text-gray-200"
                      }`}>
                        {m.label}
                      </span>
                    )}
                    
                    {/* Tooltip cuando está colapsado */}
                    {!open && (
                      <div className="absolute left-full ml-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                        {m.label}
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer con información del usuario (siempre visible en la parte inferior) */}
      {user && (
        <div className="flex-shrink-0 p-4 border-t-2 border-[#003DA5]/20 dark:border-[#003DA5]/30 bg-gradient-to-r from-[#003DA5]/5 to-transparent">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#003DA5] flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
              {user.first_name?.[0] || user.username?.[0] || "?"}{user.last_name?.[0] || ""}
            </div>
            {open && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {(user.first_name && user.last_name) ? `${user.first_name} ${user.last_name}` : user.username || "Usuario"}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user.rol}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
