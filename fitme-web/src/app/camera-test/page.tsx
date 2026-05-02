"use client";

import { useState, useRef } from "react";

export default function CameraTest() {
  const [status, setStatus] = useState("Aguardando...");
  const [error, setError] = useState("");
  const [imageData, setImageData] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = async () => {
    setStatus("Solicitando câmera...");
    setError("");

    if (!navigator.mediaDevices) {
      setError("navigator.mediaDevices não disponível. Precisa de HTTPS ou localhost.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStatus(`Câmera obtida! Tracks: ${stream.getTracks().length}`);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          setStatus(
            `Vídeo carregado: ${videoRef.current!.videoWidth}x${videoRef.current!.videoHeight}`
          );
          videoRef.current!.play();
        };
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Erro: ${msg}`);
      setStatus("Falhou");
    }
  };

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) {
      setError("Video ou canvas não disponível");
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.videoWidth === 0) {
      setError(`videoWidth=0, readyState=${video.readyState}`);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
    setImageData(dataUrl);
    setStatus(`Capturado! ${canvas.width}x${canvas.height}`);
  };

  return (
    <div className="p-8 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-4">Teste de Câmera</h1>

      <p className="mb-2 text-sm">
        <strong>Status:</strong> {status}
      </p>
      {error && (
        <p className="mb-2 text-sm text-red-600">
          <strong>Erro:</strong> {error}
        </p>
      )}

      <div className="flex gap-2 mb-4">
        <button
          onClick={startCamera}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Abrir Câmera
        </button>
        <button
          onClick={capture}
          className="px-4 py-2 bg-green-600 text-white rounded"
        >
          Capturar Frame
        </button>
      </div>

      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full border-2 border-gray-300 rounded mb-4 bg-black"
        style={{ minHeight: 200 }}
      />

      <canvas ref={canvasRef} className="hidden" />

      {imageData && (
        <div>
          <p className="text-sm font-medium mb-2">Imagem capturada:</p>
          <img src={imageData} alt="Captura" className="w-full rounded border" />
        </div>
      )}
    </div>
  );
}
