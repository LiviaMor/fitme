"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Camera, RotateCcw, Loader2, CheckCircle, Circle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ANGLES = [
  { deg: 0, label: "Frente", instruction: "Posicione-se dentro da silhueta, de frente" },
  { deg: 90, label: "Lado Dir.", instruction: "Gire para a direita (perfil)" },
  { deg: 180, label: "Costas", instruction: "Fique de costas para a câmera" },
  { deg: 270, label: "Lado Esq.", instruction: "Gire para a esquerda (perfil)" },
];

// Silhuetas SVG para cada ângulo
const SILHOUETTES: Record<number, string> = {
  0: `M50,8 C50,8 44,10 42,14 C40,18 40,22 42,24 C44,26 46,26 48,28
      L48,32 C44,33 38,36 36,40 C34,44 34,48 34,52
      L34,70 C34,72 36,74 38,74 L38,92 C38,94 40,96 42,96
      L42,96 C42,96 44,96 44,94 L44,92 L44,74
      L56,74 L56,92 C56,94 56,96 58,96 L58,96
      C60,96 62,94 62,92 L62,74 C64,74 66,72 66,70
      L66,52 C66,48 66,44 64,40 C62,36 56,33 52,32
      L52,28 C54,26 56,26 58,24 C60,22 60,18 58,14
      C56,10 50,8 50,8 Z`,
  90: `M46,8 C46,8 42,10 41,14 C40,18 40,22 42,24 C43,26 44,27 45,28
       L45,32 C42,33 38,36 37,40 C36,44 36,48 36,52
       L36,70 C36,72 37,74 38,74 L40,92 C40,94 41,96 42,96
       L44,96 C45,96 46,94 46,92 L45,74
       L55,74 L56,92 C56,94 57,96 58,96 L60,96
       C61,96 62,94 62,92 L62,74 C63,74 64,72 64,70
       L64,52 C64,48 63,44 62,40 C60,36 56,33 54,32
       L54,28 C55,26 56,24 56,22 C56,18 54,14 52,10
       C50,8 46,8 46,8 Z`,
  180: `M50,8 C50,8 44,10 42,14 C40,18 40,22 42,24 C44,26 46,26 48,28
        L48,32 C44,33 38,36 36,40 C34,44 34,48 34,52
        L34,70 C34,72 36,74 38,74 L38,92 C38,94 40,96 42,96
        L42,96 C42,96 44,96 44,94 L44,92 L44,74
        L56,74 L56,92 C56,94 56,96 58,96 L58,96
        C60,96 62,94 62,92 L62,74 C64,74 66,72 66,70
        L66,52 C66,48 66,44 64,40 C62,36 56,33 52,32
        L52,28 C54,26 56,26 58,24 C60,22 60,18 58,14
        C56,10 50,8 50,8 Z`,
  270: `M54,8 C54,8 58,10 59,14 C60,18 60,22 58,24 C57,26 56,27 55,28
        L55,32 C58,33 62,36 63,40 C64,44 64,48 64,52
        L64,70 C64,72 63,74 62,74 L60,92 C60,94 59,96 58,96
        L56,96 C55,96 54,94 54,92 L55,74
        L45,74 L44,92 C44,94 43,96 42,96 L40,96
        C39,96 38,94 38,92 L38,74 C37,74 36,72 36,70
        L36,52 C36,48 37,44 38,40 C40,36 44,33 46,32
        L46,28 C45,26 44,24 44,22 C44,18 46,14 48,10
        C50,8 54,8 54,8 Z`,
};

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
  const [step, setStep] = useState(0);
  const [captures, setCaptures] = useState<Blob[]>([]);
  const [heightCm, setHeightCm] = useState(170);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = useCallback(async () => {
    setError(null);
    try {
      // Tentar câmera traseira primeiro (melhor para corpo inteiro)
      // Fallback para qualquer câmera disponível
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
      } catch {
        // Fallback: qualquer câmera
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setStreaming(true);
      }
    } catch (err) {
      setError(
        "Não foi possível acessar a câmera. Verifique as permissões do navegador."
      );
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
    // Countdown de 3 segundos antes de capturar
    setCountdown(3);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          // Capturar
          doCapture();
          return null;
        }
        return prev - 1;
      });
    }, 1000);
  }, [step, captures, stopCamera]);

  const doCapture = () => {
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
          const newCaptures = [...captures, blob];
          setCaptures(newCaptures);

          if (step < 3) {
            setStep((s) => s + 1);
          } else {
            stopCamera();
            processFrames(newCaptures);
          }
        }
      },
      "image/jpeg",
      0.92
    );
  };

  const processFrames = async (blobs: Blob[]) => {
    setStep(4);
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
      setError("API não disponível. Verifique se o servidor está rodando.");
      setStep(0);
    }
  };

  const reset = () => {
    setStep(0);
    setCaptures([]);
    setResult(null);
    setError(null);
    setCountdown(null);
    stopCamera();
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  const currentAngle = ANGLES[step]?.deg ?? 0;

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
        {step < 4 && !streaming && (
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
        {step < 5 && step !== 4 && (
          <div className="flex justify-center gap-4 mb-6">
            {ANGLES.map((angle, i) => (
              <div key={angle.deg} className="flex flex-col items-center gap-1">
                {i < step ? (
                  <CheckCircle size={24} className="text-green-500" />
                ) : i === step ? (
                  <Circle size={24} className="text-purple-500 animate-pulse" />
                ) : (
                  <Circle size={24} className="text-gray-300" />
                )}
                <span className="text-xs text-gray-500">{angle.label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Camera with silhouette overlay */}
        {step < 4 && (
          <div className="relative max-w-md mx-auto">
            {streaming ? (
              <div className="relative overflow-hidden rounded-2xl border-4 border-purple-300 bg-black">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-auto mirror"
                  style={{ transform: "scaleX(-1)" }}
                />

                {/* Silhueta de guia */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <svg
                    viewBox="0 0 100 100"
                    className="w-48 h-80 sm:w-56 sm:h-96 opacity-50"
                    fill="none"
                    stroke="rgba(168, 85, 247, 0.7)"
                    strokeWidth="0.8"
                    strokeDasharray="2 1"
                  >
                    <path d={SILHOUETTES[currentAngle] || SILHOUETTES[0]} />
                  </svg>
                </div>

                {/* Guias de alinhamento */}
                <div className="absolute inset-0 pointer-events-none">
                  {/* Linha central vertical */}
                  <div className="absolute left-1/2 top-4 bottom-4 w-px bg-purple-400/30" />
                  {/* Linha de pés */}
                  <div className="absolute bottom-[12%] left-[15%] right-[15%] h-px bg-green-400/50" />
                  {/* Linha de cabeça */}
                  <div className="absolute top-[8%] left-[15%] right-[15%] h-px bg-green-400/50" />
                </div>

                {/* Countdown overlay */}
                {countdown !== null && (
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                    <span className="text-7xl font-bold text-white animate-ping">
                      {countdown}
                    </span>
                  </div>
                )}

                {/* Instruction bar */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 pt-8 text-center">
                  <p className="font-medium text-white text-lg">
                    {ANGLES[step].instruction}
                  </p>
                  <p className="text-sm text-purple-200 mt-1">
                    Encaixe seu corpo na silhueta — Foto {step + 1}/4
                  </p>
                </div>

                {/* Capture button */}
                {countdown === null && (
                  <button
                    onClick={captureFrame}
                    className="absolute bottom-24 left-1/2 -translate-x-1/2 w-18 h-18 bg-white/90 rounded-full border-4 border-purple-500 shadow-xl hover:scale-110 active:scale-95 transition flex items-center justify-center"
                    style={{ width: 72, height: 72 }}
                  >
                    <div className="w-14 h-14 bg-purple-500 rounded-full flex items-center justify-center">
                      <Camera size={24} className="text-white" />
                    </div>
                  </button>
                )}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                <div className="mb-6">
                  {/* Preview silhouette */}
                  <svg
                    viewBox="0 0 100 100"
                    className="w-24 h-40 mx-auto opacity-30"
                    fill="rgba(168, 85, 247, 0.3)"
                    stroke="rgba(168, 85, 247, 0.5)"
                    strokeWidth="0.5"
                  >
                    <path d={SILHOUETTES[0]} />
                  </svg>
                </div>
                <p className="text-gray-600 mb-2">
                  Posicione-se a 2-3 metros da câmera
                </p>
                <p className="text-sm text-gray-400 mb-6">
                  Corpo inteiro visível • Fundo claro • Roupa justa
                </p>
                <button
                  onClick={startCamera}
                  className="px-8 py-4 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition flex items-center gap-3 mx-auto text-lg"
                >
                  <Camera size={24} />
                  Iniciar Scanner 360°
                </button>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />
          </div>
        )}

        {/* Processing */}
        {step === 4 && (
          <div className="text-center py-16">
            <Loader2 size={56} className="animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-lg text-gray-700 font-medium">
              Processando {captures.length} frames...
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Detectando ângulos e calculando circunferências 3D
            </p>
          </div>
        )}

        {/* Results */}
        {step === 5 && result && (
          <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Resultado do Scan 360°
              </h3>
              <span className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                {Math.round(result.overall_confidence * 100)}% confiança
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {[
                ["Busto", result.bust_circumference_cm, "Circunf."],
                ["Cintura", result.waist_circumference_cm, "Circunf."],
                ["Quadril", result.hip_circumference_cm, "Circunf."],
                ["Ombros", result.shoulder_width_cm, "Largura"],
                ["Gancho", result.inseam_cm, "Altura"],
                ["Calça", result.pants_length_cm, "Compr."],
                ["Camisa", result.shirt_length_cm, "Compr."],
                ["Cava", result.armhole_depth_cm, "Altura"],
              ].map(([label, value, type]) => (
                <div
                  key={label as string}
                  className="bg-white rounded-xl p-3 border border-gray-100 text-center"
                >
                  <p className="text-[10px] text-gray-400 uppercase tracking-wider">
                    {type}
                  </p>
                  <p className="text-xl font-bold text-gray-900 mt-1">
                    {value}
                    <span className="text-sm font-normal text-gray-500"> cm</span>
                  </p>
                  <p className="text-xs text-gray-600 mt-0.5">{label}</p>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 bg-purple-50 rounded-lg text-sm text-purple-700">
              <strong>Ângulos detectados:</strong>{" "}
              {result.angles_captured.map((a) => `${a}°`).join(", ")} •{" "}
              {result.frames_analyzed} frames analisados
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
