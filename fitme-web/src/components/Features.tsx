"use client";

import {
  Camera,
  Palette,
  Ruler,
  Brain,
  ShoppingBag,
  BarChart3,
} from "lucide-react";

const features = [
  {
    icon: Camera,
    title: "Escaneamento Corporal",
    description:
      "MediaPipe detecta 33 pontos do corpo em tempo real. Extrai ombros, busto, quadril e gancho com precisão de estadiômetro Welmy.",
    color: "bg-purple-100 text-purple-600",
  },
  {
    icon: Palette,
    title: "Análise de Tom de Pele",
    description:
      "OpenCV identifica o subtom (frio, quente, neutro) e recomenda cores que valorizam o cliente.",
    color: "bg-orange-100 text-orange-600",
  },
  {
    icon: Ruler,
    title: "Estadiômetro Digital",
    description:
      "Medição de altura com padrão Welmy (resolução 0.5cm). Grade milimétrica virtual para calibração precisa.",
    color: "bg-blue-100 text-blue-600",
  },
  {
    icon: Brain,
    title: "Consultoria com IA",
    description:
      "GPT-4o analisa medidas + peça e gera consultoria de estilo personalizada. Tom de consultor de moda premium.",
    color: "bg-green-100 text-green-600",
  },
  {
    icon: ShoppingBag,
    title: "Recomendação de Tamanho",
    description:
      "Compara medidas do cliente com a tabela da peça e sugere o tamanho ideal. Reduz devoluções por tamanho errado.",
    color: "bg-pink-100 text-pink-600",
  },
  {
    icon: BarChart3,
    title: "Analytics & Insights",
    description:
      "Dashboard com dados de conversão, tamanhos mais pedidos e padrões de devolução do seu catálogo.",
    color: "bg-indigo-100 text-indigo-600",
  },
];

export function Features() {
  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Tudo que seu e-commerce precisa
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Uma API completa que transforma a experiência de compra online.
            Integre em qualquer plataforma com poucos endpoints.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group p-6 rounded-2xl border border-gray-100 hover:border-purple-200 hover:shadow-lg transition-all duration-300"
            >
              <div
                className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
              >
                <feature.icon size={24} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
