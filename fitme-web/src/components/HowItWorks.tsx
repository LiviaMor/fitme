"use client";

import { Upload, Cpu, MessageSquare, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: Upload,
    step: "01",
    title: "Upload da Foto",
    description:
      "O cliente tira uma foto de corpo inteiro com a câmera do celular. Fundo claro, boa iluminação.",
  },
  {
    icon: Cpu,
    step: "02",
    title: "IA Processa",
    description:
      "MediaPipe extrai landmarks, OpenCV analisa tom de pele. Tudo em menos de 2 segundos.",
  },
  {
    icon: MessageSquare,
    step: "03",
    title: "Consultoria Gerada",
    description:
      "GPT-4o compara medidas com a peça escolhida e gera recomendação de tamanho + consultoria de estilo.",
  },
  {
    icon: CheckCircle,
    step: "04",
    title: "Compra Certeira",
    description:
      "Cliente compra com confiança. Menos devoluções, mais satisfação, maior ticket médio.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Como funciona
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            4 passos simples. Da foto à recomendação em tempo real.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((item, index) => (
            <div key={item.step} className="relative">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-purple-200 -translate-x-1/2 z-0" />
              )}

              <div className="relative z-10 text-center">
                <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-white shadow-md flex items-center justify-center border border-gray-100">
                  <item.icon size={32} className="text-purple-600" />
                </div>
                <span className="text-xs font-bold text-purple-600 uppercase tracking-wider">
                  Passo {item.step}
                </span>
                <h3 className="text-lg font-semibold text-gray-900 mt-2 mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-gray-600">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
