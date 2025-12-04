/**
 * Hook personalizado para unificar el manejo de peticiones API y errores
 */

import { useState, useCallback } from 'react'
import { useToast } from '@/components/ToastContainer'
import { useRouter } from 'next/navigation'
import { handleApiError, getRoleHomePage } from '@/lib/permissions'
import { useAuth } from '@/store/auth'

interface ApiFetchOptions extends RequestInit {
  showErrorToast?: boolean
  showSuccessToast?: boolean
  successMessage?: string
  redirectOn403?: boolean
}

interface ApiFetchResult<T> {
  data: T | null
  error: string | null
  loading: boolean
  fetchData: (url: string, options?: ApiFetchOptions) => Promise<T | null>
}

/**
 * Hook para hacer peticiones API con manejo unificado de errores
 */
export function useApiFetch<T = any>(): ApiFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const toast = useToast()
  const router = useRouter()
  const { user } = useAuth()

  const fetchData = useCallback(async (
    url: string,
    options: ApiFetchOptions = {}
  ): Promise<T | null> => {
    const {
      showErrorToast = true,
      showSuccessToast = false,
      successMessage,
      redirectOn403 = false,
      ...fetchOptions
    } = options

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(url, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
        ...fetchOptions,
      })

      // Leer respuesta como texto primero
      const text = await response.text()
      let responseData: any

      // Intentar parsear JSON
      try {
        responseData = text ? JSON.parse(text) : {}
      } catch {
        // Si no es JSON, puede ser HTML (error del servidor)
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html')) {
          responseData = {
            detail: 'Error del servidor. El backend retornó una página de error.',
            html_response: true,
          }
        } else {
          responseData = { detail: text || 'Error desconocido' }
        }
      }

      if (!response.ok) {
        // Manejar error 403
        if (response.status === 403 && redirectOn403) {
          if (showErrorToast) {
            toast.error(responseData.detail || 'Permisos insuficientes')
          }
          setTimeout(() => {
            router.push(getRoleHomePage(user?.rol))
          }, 2000)
          setError(responseData.detail || 'Permisos insuficientes')
          return null
        }

        // Manejar otros errores
        if (showErrorToast) {
          const errorMessage = responseData.detail || responseData.message || 'Error en la petición'
          toast.error(errorMessage)
        }

        setError(responseData.detail || responseData.message || 'Error en la petición')
        return null
      }

      // Éxito
      if (showSuccessToast && successMessage) {
        toast.success(successMessage)
      }

      setData(responseData)
      return responseData
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error de red'
      
      if (showErrorToast) {
        toast.error(errorMessage)
      }

      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }, [toast, router, user])

  return { data, error, loading, fetchData }
}

