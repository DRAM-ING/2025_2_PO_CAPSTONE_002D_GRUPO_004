import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import '@testing-library/jest-dom';
import EvidenceThumbnail from "@/components/EvidenceThumbnail";

// Mock de fetch global
global.fetch = vi.fn();
global.URL.createObjectURL = vi.fn((blob) => `blob:${blob}`);
global.URL.revokeObjectURL = vi.fn();

// Importar el módulo para acceder al cache si es posible
let notFoundCache: Set<string> | null = null;

describe("EvidenceThumbnail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // El cache está dentro del módulo del componente, no podemos accederlo directamente
    // Usaremos IDs únicos para cada test para evitar conflictos
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Tipos de archivo no-imagen", () => {
    it("debe mostrar icono de PDF para tipo PDF", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="PDF"
          className="test-class"
        />
      );
      expect(screen.getByText("📄")).toBeInTheDocument();
    });

    it("debe mostrar icono de hoja de cálculo para tipo HOJA_CALCULO", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="HOJA_CALCULO"
          className="test-class"
        />
      );
      expect(screen.getByText("📊")).toBeInTheDocument();
    });

    it("debe mostrar icono de documento para tipo DOCUMENTO", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="DOCUMENTO"
          className="test-class"
        />
      );
      expect(screen.getByText("📝")).toBeInTheDocument();
    });

    it("debe mostrar icono de comprimido para tipo COMPRIMIDO", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="COMPRIMIDO"
          className="test-class"
        />
      );
      expect(screen.getByText("📦")).toBeInTheDocument();
    });

    it("debe mostrar icono genérico para tipo desconocido", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="OTRO"
          className="test-class"
        />
      );
      expect(screen.getByText("📎")).toBeInTheDocument();
    });
  });

  describe("Carga de imágenes (tipo FOTO)", () => {
    it("debe mostrar spinner mientras carga", async () => {
      // Usar un ID único para evitar conflictos con el cache
      const uniqueId = `test-spinner-${Date.now()}-${Math.random()}`;
      
      let resolveFetch: any;
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = () => {
          resolve({
            ok: true,
            headers: new Headers({ "content-type": "image/jpeg" }),
            blob: async () => new Blob(),
          });
        };
      });

      (global.fetch as any).mockImplementation(() => fetchPromise);

      render(
        <EvidenceThumbnail
          evidenciaId={uniqueId}
          tipo="FOTO"
          className="test-class"
        />
      );
      
      // Verificar que el spinner aparece inmediatamente (loading es true inicialmente)
      // El componente muestra loading=true al inicio para tipo FOTO
      await waitFor(() => {
        const spinner = document.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
      }, { timeout: 100 });
      
      // Resolver el fetch después de verificar el spinner
      resolveFetch();
      
      // Esperar a que termine de cargar (el spinner desaparece)
      await waitFor(() => {
        expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verificar que la imagen se cargó correctamente
      const image = screen.getByRole("img", { name: /Evidencia/i });
      expect(image).toBeInTheDocument();
    });

    it("debe mostrar imagen cuando se carga correctamente", async () => {
      const mockBlob = new Blob(["test"], { type: "image/jpeg" });
      (global.fetch as any).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "image/jpeg" }),
        blob: async () => mockBlob,
      });

      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="FOTO"
          alt="Test image"
          className="test-class"
        />
      );

      await waitFor(() => {
        const img = screen.getByAltText("Test image");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("loading", "lazy");
      });
    });

    it("debe manejar error 404 y cachear el resultado", async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ detail: "Not found" }),
      });

      const { rerender } = render(
        <EvidenceThumbnail
          evidenciaId="test-404-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Archivo no disponible/i)).toBeInTheDocument();
      });

      // Re-renderizar con el mismo ID - no debe hacer fetch nuevamente
      rerender(
        <EvidenceThumbnail
          evidenciaId="test-404-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      // Verificar que fetch solo se llamó una vez
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it("debe manejar errores de conexión", async () => {
      (global.fetch as any).mockRejectedValue(new Error("Network error"));

      render(
        <EvidenceThumbnail
          evidenciaId="test-error-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });

    it("debe manejar errores HTTP diferentes a 404", async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ detail: "Server error" }),
      });

      render(
        <EvidenceThumbnail
          evidenciaId="test-500-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Error al cargar/i)).toBeInTheDocument();
      });
    });

    it("debe manejar respuesta JSON con download_url", async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "application/json" }),
        text: async () =>
          JSON.stringify({ download_url: "https://example.com/image.jpg" }),
      });

      render(
        <EvidenceThumbnail
          evidenciaId="test-json-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        const img = screen.getByAltText("Evidencia");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("src", "https://example.com/image.jpg");
      });
    });

    it("debe limpiar blob URL al desmontar", async () => {
      const mockBlob = new Blob(["test"], { type: "image/jpeg" });
      (global.fetch as any).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "image/jpeg" }),
        blob: async () => mockBlob,
      });

      const { unmount } = render(
        <EvidenceThumbnail
          evidenciaId="test-cleanup-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        expect(screen.getByAltText("Evidencia")).toBeInTheDocument();
      });

      unmount();

      // Verificar que se llamó revokeObjectURL
      expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });

    it("debe manejar error al cargar imagen en el elemento img", async () => {
      const mockBlob = new Blob(["test"], { type: "image/jpeg" });
      (global.fetch as any).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "image/jpeg" }),
        blob: async () => mockBlob,
      });

      render(
        <EvidenceThumbnail
          evidenciaId="test-img-error-id"
          tipo="FOTO"
          className="test-class"
        />
      );

      await waitFor(() => {
        const img = screen.getByAltText("Evidencia");
        expect(img).toBeInTheDocument();
      });

      // Simular error en la carga de la imagen
      const img = screen.getByAltText("Evidencia");
      const errorEvent = new Event("error");
      img.dispatchEvent(errorEvent);

      await waitFor(() => {
        expect(screen.getByText(/Error al cargar imagen/i)).toBeInTheDocument();
      });
    });
  });

  describe("Props y clases CSS", () => {
    it("debe aplicar className correctamente", () => {
      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="PDF"
          className="custom-class"
        />
      );
      const container = screen.getByText("📄").parentElement;
      expect(container).toHaveClass("custom-class");
    });

    it("debe usar alt text personalizado", async () => {
      const mockBlob = new Blob(["test"], { type: "image/jpeg" });
      (global.fetch as any).mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-type": "image/jpeg" }),
        blob: async () => mockBlob,
      });

      render(
        <EvidenceThumbnail
          evidenciaId="test-id"
          tipo="FOTO"
          alt="Imagen personalizada"
          className="test-class"
        />
      );

      await waitFor(() => {
        expect(screen.getByAltText("Imagen personalizada")).toBeInTheDocument();
      });
    });
  });
});

