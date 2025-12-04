import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// Mock Next.js router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
};

const mockUseParams = vi.fn(() => ({}));

vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => mockUseParams(),
}))

// Mock fetch globally
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock as any

// Mock useAuth store
// Zustand hooks retornan funciones, así que necesitamos mockear el hook correctamente
const mockAuthStore = {
  user: { id: '1', username: 'test', rol: 'ADMIN' as const },
  setUser: vi.fn(),
  allowed: vi.fn(() => true),
  hasRole: vi.fn(() => true),
  isLogged: () => true,  // Función que retorna boolean, no un mock
  refreshMe: vi.fn(() => Promise.resolve()),
};

vi.mock('@/store/auth', () => ({
  useAuth: () => mockAuthStore,
}))

