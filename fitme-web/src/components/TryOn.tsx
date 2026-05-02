"use client";

import { useState, useRef } from "react";
import { Camera, Link, Loader2, Shirt, Sparkles } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const GARMENT_TYPES = [
  { value: "camiseta", label: "Camiseta" },
  { value: "camisa", label: "Camisa" },
  { value: "vestido", label: "Vestido" },
  { value: "calca", label: "Calça" },
  { value: "saia", label: "Saia" },
  { value: "blazer", label: "Blazer" },
  { value: "jaqueta", label: "Jaqueta" },
];

export function TryOn() {
  const [personImage, setPersonImage] = useState<string | null>(null);
  const [personFile, setPersonFile] = useState<File | null>(null);
  const [garmentUrl, setGarmentUrl] = useState("");
  const [garmentType, setGarmentType] = useState("camiseta");
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPersonFile(file);
      setPersonImage(URL.createObjectURL(file));
      setResultImage(null);
      setError(null);
    }
  };

  const handleTryOn = async () => {
    if (!personFile || !garmentUrl) return;
    setLoading(true);
    setError(null);
    setResultImage(null);

    try {
      const formData = new FormData();
      formData.append("photo", personFile);
      formData.append("garment_url", garmentUrl);
      formData.append("garment_type", garmentType);
      formData.append("opacity", "0.85");

      const response = await fetch(`${API_URL}/api/v1/tryon/url/base64`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResultImage(`data:image/png;base64,${data.image_base64}`);
      } else {
        const err = await response.json();
        setError(err.detail || "Erro no try-on.");
      }
    } catch {
      setError("API não disponível. Verifique a conexão.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="tryon" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            👗 Provador Virtual
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Suba sua foto e cole o link da roupa. A IA veste a peça em você.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {/* 1. Foto do cliente */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Camera size={18} className="text-purple-600" />
              Sua Foto
            </h3>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center cursor-pointer hover:border-purple-400 transition min-h-[250px] flex flex-col items-center justify-center"
            >
              {personImage ? (
                <img
                  src={personImage}
                  alt="Sua foto"
                  className="max-h-56 rounded-lg object-contain"
                />
              ) : (
                <>
                  <Camera size={32} className="text-gray-300 mb-2" />
                  <p className="text-sm text-gray-500">Clique para enviar</p>
                  <p className="text-xs text-gray-400">Corpo inteiro, fundo claro</p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* 2. Link da roupa */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Shirt size={18} className="text-purple-600" />
              Roupa do E-commerce
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600 mb-1 block">
                  URL da imagem da roupa
                </label>
                <div className="flex items-center gap-2">
                  <Link size={16} className="text-gray-400 flex-shrink-0" />
                  <input
                    type="url"
                    value={garmentUrl}
                    onChange={(e) => setGarmentUrl(e.target.value)}
                    placeholder="https://loja.com/roupa.jpg"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 mb-1 block">
                  Tipo de peça
                </label>
                <select
                  value={garmentType}
                  onChange={(e) => setGarmentType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {GARMENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              {garmentUrl && (
                <div className="border border-gray-200 rounded-lg p-2">
                  <img
                    src={garmentUrl}
                    alt="Preview da roupa"
                    className="max-h-40 mx-auto rounded object-contain"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                </div>
              )}
            </div>

            <button
              onClick={handleTryOn}
              disabled={!personFile || !garmentUrl || loading}
              className="w-full py-3 px-6 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Vestindo...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Experimentar
                </>
              )}
            </button>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* 3. Resultado */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles size={18} className="text-purple-600" />
              Resultado
            </h3>
            <div className="bg-white border border-gray-200 rounded-xl min-h-[250px] flex items-center justify-center p-4">
              {resultImage ? (
                <img
                  src={resultImage}
                  alt="Try-on result"
                  className="max-h-72 rounded-lg object-contain"
                />
              ) : (
                <div className="text-center">
                  <Shirt size={40} className="text-gray-200 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">
                    O resultado aparecerá aqui
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
