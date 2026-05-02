"use client";

import { useState, useRef, useCallback } from "react";
import { Camera, RotateCcw, Loader2, CheckCircle, Circle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ANGLES = [
  { deg: 0, label: "Frente", instruction: "Fique de frente para a câmera" },
  { deg: 90, label: "Lado Dir.", instruction: "Vire para a direita (perfil)" },
  { deg: 180, label: "Costas", instruction: "Fique de costas" },
  { deg: 270, label: "Lado Esq.", instruction: "Vire para a esquerda (perfil)" },
];

interface ScanResult {
  bust_circumference_cm: number;
  waist_circumference_cm: number;
  hip_circumference_cm: number;
  height_cm: number;
  shoulder_width_cm: number;
  inseam_cm: number;
  pants_length_cm: number;
  shirt_length_cm: number;
  armhole_depth_cm: number;
  frames_analyzed: number;
  angles_captured: number[];
  overall_confidence: number;
}

export function Scanner360() {
  const [step, setStep] = useState(0); // 0-3 = capturando, 4 = processando, 5 = resultado
  const [captures, setCaptures] = useState<Blob[]>([]);
  const [heightCm, setHeightCm] = useState(170);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 720, height: 1280 },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setStreaming(true);
      }
    } catch {
      setError("Não foi possível acessar a câmera.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((t) => t.stop());
      videoRef.current.srcObject = null;
      setStreaming(false);
    }
  }, []);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCaptures((prev) => [...prev, blob]);
          if (step < 3) {
            setStep((s) => s + 1);
          } else {
            // Todas as 4 fotos capturadas, processar
            stopCamera();
            processFrames([...captures, blob]);
          }
        }
      },
      "image/jpeg",
      0.9
    );
  }, [step, captures, stopCamera]);

  const processFrames = async (blobs: Blob[]) => {
    setStep(4); // processando
    setError(null);

    try {
      const formData = new FormData();
      blobs.forEach((blob, i) => {
        formData.append("frames", blob, `frame_${i}.jpg`);
      });
      formData.append("height_cm", heightCm.toString());

      const response = await fetch(`${API_URL}/api/v1/scan360/multi`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        setStep(5);
      } else {
        const err = await response.json();
        setError(err.detail || "Erro no processamento.");
        setStep(0);
      }
    } catch {
      setError("API não disponível.");
      setStep(0);
    }
  };

  const reset = () => {
    setStep(0);
    setCaptures([]);
    setResult(null);
    setError(null);
    stopCamera();
  };

  return (
    <section id="scanner360" className="py-20 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            📐 Scanner 360°
          </h2>
          <p className="text-lg text-gray-600">
            Gire lentamente e capture 4 fotos. A IA calcula suas medidas reais.
          </p>
        </div>

        {/* Altura input */}
        {step < 4 && (
          <div className="max-w-xs mx-auto mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-1">
              Sua altura (cm)
            </label>
            <input
              type="number"
              value={heightCm}
              onChange={(e) => setHeightCm(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg text-center text-lg"
              min={100}
              max={220}
            />
          </div>
        )}

        {/* Progress indicators */}
        {step < 5 && (
          <div className="flex justify-center gap-4 mb-6">
            {ANGLES.map((angle, i) => (
              <div key={angle.deg} className="flex flex-col items-center gap-1">
                {i < step ? (
                  <CheckCircle size={24} className="text-green-500" />
                ) : i === step && step < 4 ? (
                  <Circle size={24} className="text-purple-500 animate-pulse" />
                ) : (
                  <Circle size={24} className="text-gray-300" />
                )}
                <span className="text-xs text-gray-500">{angle.label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Camera / Instructions */}
        {step < 4 && (
          <div className="relative max-w-md mx-auto">
            {streaming ? (
              <div className="relative">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full rounded-2xl border-4 border-purple-200"
                />
                {/* Overlay instruction */}
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white p-4 rounded-b-2xl text-center">
                  <p className="font-medium">{ANGLES[step].instruction}</p>
                  <p className="text-sm text-gray-300">
                    Foto {step + 1} de 4 — {ANGLES[step].label}
                  </p>
                </div>
                {/* Capture button */}
                <button
                  onClick={captureFrame}
                  className="absolute bottom-20 left-1/2 -translate-x-1/2 w-16 h-16 bg-white rounded-full border-4 border-purple-500 shadow-lg hover:scale-110 transition flex items-center justify-center"
                >
                  <div className="w-12 h-12 bg-purple-500 rounded-full" />
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <button
                  onClick={startCamera}
                  className="px-6 py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition flex items-center gap-2 mx-auto"
                >
                  <Camera size={20} />
                  Iniciar Scanner 360°
                </button>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />
          </div>
        )}

        {/* Processing */}
        {step === 4 && (
          <div className="text-center py-12">
            <Loader2 size={48} className="animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-gray-600">Processando {captures.length} frames...</p>
            <p className="text-sm text-gray-400">Calculando circunferências 3D</p>
          </div>
        )}

        {/* Results */}
        {step === 5 && result && (
          <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-semibold text-gray-900">Resultado do Scan 360°</h3>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                {Math.round(result.overall_confidence * 100)}% confiança
              </span>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                ["Busto", result.bust_circumference_cm, "Circunferência"],
                ["Cintura", result.waist_circumference_cm, "Circunferência"],
                ["Quadril", result.hip_circumference_cm, "Circunferência"],
                ["Ombros", result.shoulder_width_cm, "Largura"],
                ["Gancho", result.inseam_cm, "Altura"],
                ["Calça", result.pants_length_cm, "Comprimento"],
                ["Camisa", result.shirt_length_cm, "Comprimento"],
                ["Cava", result.armhole_depth_cm, "Altura"],
              ].map(([label, value, type]) => (
                <div
                  key={label as string}
                  className="bg-white rounded-xl p-4 border border-gray-100"
                >
                  <p className="text-xs text-gray-500 uppercase">{type}</p>
                  <p className="text-2xl font-bold text-gray-900">{value} cm</p>
                  <p className="text-sm text-gray-600">{label}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-center justify-between text-sm text-gray-500">
              <span>{result.frames_analyzed} frames analisados</span>
              <span>Ângulos: {result.angles_captured.join("°, ")}°</span>
            </div>

            <button
              onClick={reset}
              className="mt-6 w-full py-3 border border-gray-200 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition flex items-center justify-center gap-2"
            >
              <RotateCcw size={18} />
              Escanear novamente
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 text-center">
            {error}
          </div>
        )}
      </div>
    </section>
  );
}
