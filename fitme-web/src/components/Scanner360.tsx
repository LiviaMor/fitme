"use client";

import { useState, useRef, useEffect } from "react";
import { Camera, RotateCcw, Loader2, CheckCircle, Circle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ANGLES = [
  { label: "Frente", instruction: "Fique de frente, braços afastados" },
  { label: "Lado Dir.", instruction: "Vire para a direita (perfil)" },
  { label: "Costas", instruction: "Fique de costas" },
  { label: "Lado Esq.", instruction: "Vire para a esquerda (perfil)" },
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
  const [step, setStep] = useState(0);
  const [cameraOn, setCameraOn] = useState(false);
  const [captures, setCaptures] = useState<string[]>([]);
  const [heightCm, setHeightCm] = useState(170);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Refs para valores atuais (evita stale closures no toBlob callback)
  const capturesRef = useRef<string[]>([]);
  const blobsRef = useRef<Blob[]>([]);
  const stepRef = useRef(0);

  // Try-on state
  const [garmentUrl, setGarmentUrl] = useState("");
  const [garmentType, setGarmentType] = useState("camiseta");
  const [tryonResult, setTryonResult] = useState<string | null>(null);
  const [tryonLoading, setTryonLoading] = useState(false);

  // Abrir câmera
  const openCamera = async () => {
    setError(null);
    try {
      // Pedir 1080x1920 (retrato celular) como ideal
      // Se a câmera não suportar, aceita o que tiver
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1080 },
          height: { ideal: 1920 },
          facingMode: { ideal: "environment" },
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraOn(true);
    } catch {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setCameraOn(true);
      } catch (e: unknown) {
        setError(`Câmera: ${e instanceof Error ? e.message : "não disponível"}`);
      }
    }
  };

  // Fechar câmera
  const closeCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  };

  // Capturar frame
  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) {
      setError("Elementos de vídeo/canvas não encontrados.");
      return;
    }

    if (video.readyState < 2 || video.videoWidth === 0) {
      setError("Vídeo não pronto. Aguarde a câmera carregar.");
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.85);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Falha ao capturar frame.");
          return;
        }

        // Usar refs para valores atuais
        const newCaptures = [...capturesRef.current, dataUrl];
        const newBlobs = [...blobsRef.current, blob];
        const newStep = stepRef.current + 1;

        // Atualizar refs
        capturesRef.current = newCaptures;
        blobsRef.current = newBlobs;
        stepRef.current = newStep;

        // Atualizar state (para re-render)
        setCaptures(newCaptures);
        setStep(newStep);

        // Se completou 4 fotos, enviar
        if (newBlobs.length >= 4) {
          closeCamera();
          sendToAPI(newBlobs);
        }
      },
      "image/jpeg",
      0.9
    );
  };

  // Enviar para API
  const sendToAPI = async (frameBlobs: Blob[]) => {
    setProcessing(true);
    setError(null);
    try {
      const formData = new FormData();
      frameBlobs.forEach((b, i) => formData.append("frames", b, `frame${i}.jpg`));
      formData.append("height_cm", heightCm.toString());

      const res = await fetch(`${API_URL}/api/v1/scan360/multi`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setResult(await res.json());
      } else {
        const err = await res.json();
        setError(err.detail || "Erro na API");
      }
    } catch {
      setError("API não disponível.");
    } finally {
      setProcessing(false);
    }
  };

  // Reset
  const reset = () => {
    closeCamera();
    setStep(0);
    stepRef.current = 0;
    setCaptures([]);
    capturesRef.current = [];
    blobsRef.current = [];
    setResult(null);
    setError(null);
    setProcessing(false);
    setTryonResult(null);
    setGarmentUrl("");
  };

  // Try-on: usa a primeira foto (frontal) + URL da roupa
  const doTryOn = async () => {
    if (!blobsRef.current[0] || !garmentUrl) return;
    setTryonLoading(true);
    setError(null);
    setTryonResult(null);

    try {
      const formData = new FormData();
      formData.append("photo", blobsRef.current[0], "front.jpg");
      formData.append("garment_url", garmentUrl);
      formData.append("garment_type", garmentType);
      formData.append("opacity", "0.85");

      const res = await fetch(`${API_URL}/api/v1/tryon/url/base64`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setTryonResult(`data:image/png;base64,${data.image_base64}`);
      } else {
        const err = await res.json();
        setError(err.detail || "Erro no try-on.");
      }
    } catch {
      setError("API não disponível para try-on.");
    } finally {
      setTryonLoading(false);
    }
  };

  // Cleanup
  useEffect(() => () => { closeCamera(); }, []);

  // Gerar marcas do estadiômetro (régua lateral)
  const rulerMarks = [];
  for (let cm = 0; cm <= 200; cm += 10) {
    rulerMarks.push(cm);
  }

  return (
    <section id="scanner360" className="py-20 bg-white">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            📐 Scanner 360°
          </h2>
          <p className="text-lg text-gray-600">
            Capture 4 fotos girando. A IA calcula circunferências reais.
          </p>
        </div>

        {/* Resultado */}
        {result && (
          <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Medidas 360°</h3>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                {Math.round(result.overall_confidence * 100)}% confiança
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Busto", result.bust_circumference_cm],
                ["Cintura", result.waist_circumference_cm],
                ["Quadril", result.hip_circumference_cm],
                ["Ombros", result.shoulder_width_cm],
                ["Gancho", result.inseam_cm],
                ["Calça", result.pants_length_cm],
                ["Camisa", result.shirt_length_cm],
                ["Cava", result.armhole_depth_cm],
              ].map(([label, value]) => (
                <div key={label as string} className="bg-white rounded-lg p-3 text-center border">
                  <p className="text-xl font-bold text-gray-900">{value}<span className="text-xs text-gray-400"> cm</span></p>
                  <p className="text-xs text-gray-500">{label}</p>
                </div>
              ))}
            </div>
            <button onClick={reset} className="mt-4 w-full py-2 border rounded-lg text-gray-600 hover:bg-gray-50 flex items-center justify-center gap-2">
              <RotateCcw size={16} /> Refazer
            </button>

            {/* Try-On após medidas */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                👗 Experimentar uma roupa
              </h3>

              <div className="grid sm:grid-cols-2 gap-4">
                {/* Input da roupa */}
                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-gray-600 block mb-1">URL da imagem da roupa</label>
                    <input
                      type="url"
                      value={garmentUrl}
                      onChange={(e) => { setGarmentUrl(e.target.value); setTryonResult(null); }}
                      placeholder="https://loja.com/camisa.jpg"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 block mb-1">Tipo de peça</label>
                    <select
                      value={garmentType}
                      onChange={(e) => setGarmentType(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {[
                        ["camiseta", "Camiseta"], ["camisa", "Camisa"], ["vestido", "Vestido"],
                        ["calca", "Calça"], ["saia", "Saia"], ["blazer", "Blazer"], ["jaqueta", "Jaqueta"],
                        ["corpo_inteiro", "Corpo Inteiro"],
                      ].map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                      ))}
                    </select>
                  </div>

                  {garmentUrl && (
                    <div className="border rounded-lg p-2 bg-white">
                      <img
                        src={garmentUrl}
                        alt="Roupa"
                        className="max-h-32 mx-auto object-contain rounded"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                      />
                    </div>
                  )}

                  <button
                    onClick={doTryOn}
                    disabled={!garmentUrl || tryonLoading}
                    className="w-full py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
                  >
                    {tryonLoading ? (
                      <><Loader2 size={18} className="animate-spin" /> Vestindo...</>
                    ) : (
                      "👗 Experimentar"
                    )}
                  </button>
                </div>

                {/* Resultado try-on */}
                <div className="bg-white border rounded-xl p-3 min-h-[200px] flex items-center justify-center">
                  {tryonResult ? (
                    <img src={tryonResult} alt="Try-on" className="max-h-80 rounded-lg object-contain" />
                  ) : captures[0] ? (
                    <div className="text-center">
                      <img src={captures[0]} alt="Sua foto" className="max-h-48 rounded-lg object-contain mx-auto mb-2 opacity-50" />
                      <p className="text-xs text-gray-400">Cole o link da roupa e clique Experimentar</p>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400">Resultado aparecerá aqui</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Processing */}
        {processing && (
          <div className="text-center py-16">
            <Loader2 size={48} className="animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-gray-600">Calculando medidas 3D...</p>
          </div>
        )}

        {/* Scanner UI */}
        {!result && !processing && (
          <>
            {/* Altura */}
            {!cameraOn && (
              <div className="max-w-xs mx-auto mb-6">
                <label className="text-sm font-medium text-gray-700 block mb-1">Sua altura (cm)</label>
                <input
                  type="number"
                  value={heightCm}
                  onChange={(e) => setHeightCm(Number(e.target.value))}
                  className="w-full px-4 py-2 border rounded-lg text-center text-lg"
                  min={100} max={220}
                />
              </div>
            )}

            {/* Progress */}
            <div className="flex justify-center gap-3 mb-6">
              {ANGLES.map((a, i) => (
                <div key={i} className="flex flex-col items-center gap-1">
                  {i < step ? (
                    <CheckCircle size={22} className="text-green-500" />
                  ) : i === step ? (
                    <Circle size={22} className="text-purple-500 animate-pulse" />
                  ) : (
                    <Circle size={22} className="text-gray-300" />
                  )}
                  <span className="text-[10px] text-gray-500">{a.label}</span>
                </div>
              ))}
            </div>

            {/* Camera view */}
            <div className="max-w-sm mx-auto">
              {/* Video container - 9:16 (1080x1920) */}
              <div className="relative bg-black rounded-2xl overflow-hidden border-2 border-purple-300" style={{ aspectRatio: "9/16", maxHeight: "75vh" }}>
                {/* Video sempre no DOM */}
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`absolute inset-0 w-full h-full object-contain ${cameraOn ? "opacity-100" : "opacity-0"}`}
                  style={{ transform: "scaleX(-1)" }}
                />

                {/* Placeholder quando câmera está off */}
                {!cameraOn && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 rounded-2xl">
                    <svg viewBox="0 0 100 100" className="w-20 h-32 opacity-20 mb-4" fill="gray" stroke="gray" strokeWidth="0.3">
                      <path d="M50,5 C47,5 43,8 41,12 C39,16 39,20 41,23 C43,25 45,26 47,27 L47,31 C43,32 38,35 36,39 C34,43 33,47 33,52 L33,68 C33,70 34,72 36,72 L36,92 C36,94 38,96 40,96 C42,96 43,94 43,92 L43,72 L57,72 L57,92 C57,94 58,96 60,96 C62,96 64,94 64,92 L64,72 C66,72 67,70 67,68 L67,52 C67,47 66,43 64,39 C62,35 57,32 53,31 L53,27 C55,26 57,25 59,23 C61,20 61,16 59,12 C57,8 53,5 50,5 Z" />
                    </svg>
                    <p className="text-gray-400 text-sm">Câmera desligada</p>
                  </div>
                )}

                {/* Overlay: grade quadriculada + estadiômetro */}
                {cameraOn && (
                  <>
                    {/* Grade quadriculada - 10cm cada quadrado, 0-200cm */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                      {/* Linhas horizontais a cada 10cm (20 divisões para 200cm) */}
                      {Array.from({ length: 21 }, (_, i) => {
                        const y = 3 + (i / 20) * 94; // 3% top margin, 94% usable
                        const cm = 200 - i * 10;
                        const isMajor = cm % 50 === 0;
                        return (
                          <line
                            key={`h${i}`}
                            x1="0%" y1={`${y}%`}
                            x2="100%" y2={`${y}%`}
                            stroke={isMajor ? "rgba(0,255,100,0.35)" : "rgba(0,255,100,0.12)"}
                            strokeWidth={isMajor ? "1" : "0.5"}
                          />
                        );
                      })}
                      {/* Linhas verticais (dividir em 10 colunas) */}
                      {Array.from({ length: 11 }, (_, i) => {
                        const x = (i / 10) * 100;
                        return (
                          <line
                            key={`v${i}`}
                            x1={`${x}%`} y1="3%"
                            x2={`${x}%`} y2="97%"
                            stroke={i === 5 ? "rgba(255,255,255,0.2)" : "rgba(0,255,100,0.12)"}
                            strokeWidth={i === 5 ? "1" : "0.5"}
                          />
                        );
                      })}
                      {/* Linha da altura do usuário (amarela) */}
                      {(() => {
                        const y = 3 + ((200 - heightCm) / 200) * 94;
                        return (
                          <line
                            x1="0%" y1={`${y}%`}
                            x2="100%" y2={`${y}%`}
                            stroke="rgba(255,220,0,0.8)"
                            strokeWidth="2"
                            strokeDasharray="8 4"
                          />
                        );
                      })()}
                    </svg>

                    {/* Labels de cm na direita */}
                    <div className="absolute right-1 top-[3%] bottom-[3%] w-8 pointer-events-none">
                      {Array.from({ length: 21 }, (_, i) => {
                        const cm = 200 - i * 10;
                        const pct = (i / 20) * 100;
                        const isMajor = cm % 50 === 0;
                        if (!isMajor) return null;
                        return (
                          <div key={cm} className="absolute right-0" style={{ top: `${pct}%`, transform: "translateY(-50%)" }}>
                            <span className="text-[9px] text-green-300 font-mono bg-black/50 px-1 rounded">
                              {cm}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Label da altura do usuário */}
                    {(() => {
                      const pct = ((200 - heightCm) / 200) * 100;
                      return (
                        <div
                          className="absolute left-1 pointer-events-none"
                          style={{ top: `${3 + pct * 0.94}%`, transform: "translateY(-100%)" }}
                        >
                          <span className="text-[10px] text-yellow-300 font-mono font-bold bg-black/70 px-1.5 py-0.5 rounded">
                            {heightCm}cm
                          </span>
                        </div>
                      );
                    })()}

                    {/* Instrução */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-6 text-center">
                      <p className="text-white font-medium">{ANGLES[step]?.instruction || "Pronto!"}</p>
                      <p className="text-purple-200 text-xs mt-1">Foto {Math.min(step + 1, 4)} de 4</p>
                    </div>
                  </>
                )}
              </div>

              {/* Botões */}
              <div className="mt-4 flex gap-3 justify-center">
                {!cameraOn ? (
                  <button
                    onClick={openCamera}
                    className="px-6 py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition flex items-center gap-2"
                  >
                    <Camera size={20} />
                    Abrir Câmera
                  </button>
                ) : step < 4 ? (
                  <button
                    onClick={capture}
                    className="px-8 py-4 bg-purple-600 text-white font-bold rounded-full hover:bg-purple-700 active:scale-95 transition flex items-center gap-2 text-lg shadow-lg"
                  >
                    <Camera size={24} />
                    Capturar ({step + 1}/4)
                  </button>
                ) : null}
              </div>

              {/* Thumbnails das capturas */}
              {captures.length > 0 && (
                <div className="flex gap-2 mt-4 justify-center">
                  {captures.map((src, i) => (
                    <img key={i} src={src} alt={`Foto ${i + 1}`} className="w-14 h-20 object-cover rounded border-2 border-purple-300" />
                  ))}
                </div>
              )}

              {/* Upload fallback */}
              {!cameraOn && (
                <div className="mt-6 text-center">
                  <p className="text-xs text-gray-400 mb-2">Ou faça upload de 2-4 fotos:</p>
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => {
                      const files = e.target.files;
                      if (files && files.length >= 2) {
                        const b: Blob[] = Array.from(files).slice(0, 8);
                        sendToAPI(b);
                      } else {
                        setError("Envie pelo menos 2 fotos.");
                      }
                    }}
                    className="text-sm text-gray-500 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:bg-purple-50 file:text-purple-700 file:text-xs cursor-pointer"
                  />
                </div>
              )}
            </div>
          </>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 text-center max-w-sm mx-auto">
            {error}
          </div>
        )}

        <canvas ref={canvasRef} className="hidden" />
      </div>
    </section>
  );
}
