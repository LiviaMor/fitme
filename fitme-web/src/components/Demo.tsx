"use client";

import { useState, useRef } from "react";
import { Upload, Camera, Loader2, Sparkles } from "lucide-react";

interface AnalysisResult {
  measurements: {
    shoulder_width_cm: number;
    bust_cm: number;
    waist_cm: number;
    hip_cm: number;
    inseam_cm: number;
    pants_length_cm: number;
    shirt_length_cm: number;
    armhole_depth_cm: number;
    height_cm: number;
  };
  skin_analysis: {
    hex_color: string;
    undertone: string;
    color_name: string;
  };
  body_type: string;
  confidence_score: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function Demo() {
  const [image, setImage] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setImage(URL.createObjectURL(selectedFile));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("photo", file);
      formData.append("height_cm", "170");

      const response = await fetch(`${API_URL}/api/v1/analyze/body`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        const err = await response.json();
        setError(err.detail || "Erro na análise. Tente outra foto.");
      }
    } catch {
      setError("API não disponível. Configure NEXT_PUBLIC_API_URL.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="demo" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Experimente agora
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Suba uma foto de corpo inteiro e veja a IA em ação.
            Fundo claro, corpo inteiro visível.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Upload area */}
          <div className="space-y-4">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="relative border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/50 transition-all min-h-[320px] flex flex-col items-center justify-center"
            >
              {image ? (
                <img
                  src={image}
                  alt="Preview"
                  className="max-h-72 rounded-xl object-contain"
                />
              ) : (
                <>
                  <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-4">
                    <Camera size={28} className="text-purple-600" />
                  </div>
                  <p className="text-gray-700 font-medium mb-1">
                    Clique para enviar uma foto
                  </p>
                  <p className="text-sm text-gray-500">
                    JPEG, PNG ou WebP • Corpo inteiro visível
                  </p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="w-full py-3 px-6 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Analisando...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Analisar com IA
                </>
              )}
            </button>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* Results */}
          <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 min-h-[320px]">
            {result ? (
              <div className="space-y-6">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles size={18} className="text-purple-600" />
                  <h3 className="font-semibold text-gray-900">Resultado da Análise</h3>
                  <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                    {Math.round(result.confidence_score * 100)}% confiança
                  </span>
                </div>

                {/* Measurements */}
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">
                    Medidas Corporais
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      ["Ombros", result.measurements.shoulder_width_cm],
                      ["Busto", result.measurements.bust_cm],
                      ["Cintura", result.measurements.waist_cm],
                      ["Quadril", result.measurements.hip_cm],
                      ["Gancho", result.measurements.inseam_cm],
                      ["Calça", result.measurements.pants_length_cm],
                      ["Camisa", result.measurements.shirt_length_cm],
                      ["Cava", result.measurements.armhole_depth_cm],
                    ].map(([label, value]) => (
                      <div
                        key={label as string}
                        className="flex justify-between bg-white rounded-lg px-3 py-2 text-sm"
                      >
                        <span className="text-gray-600">{label}</span>
                        <span className="font-medium text-gray-900">{value} cm</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Skin */}
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2 uppercase tracking-wider">
                    Tom de Pele
                  </h4>
                  <div className="flex items-center gap-3 bg-white rounded-lg px-4 py-3">
                    <div
                      className="w-10 h-10 rounded-lg border border-gray-200"
                      style={{ backgroundColor: result.skin_analysis.hex_color }}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {result.skin_analysis.color_name}
                      </p>
                      <p className="text-xs text-gray-500">
                        Subtom {result.skin_analysis.undertone} • {result.skin_analysis.hex_color}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Body type */}
                <div className="flex items-center gap-3 bg-purple-50 rounded-lg px-4 py-3">
                  <span className="text-sm text-purple-700">
                    <strong>Biotipo:</strong> {result.body_type}
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <Upload size={40} className="text-gray-300 mb-4" />
                <p className="text-gray-500 text-sm">
                  Os resultados da análise aparecerão aqui
                </p>
                <p className="text-gray-400 text-xs mt-1">
                  Envie uma foto para começar
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
