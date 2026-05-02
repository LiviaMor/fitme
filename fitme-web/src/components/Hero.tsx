"use client";

import { ArrowRight, Play, ShieldCheck, TrendingDown, Zap } from "lucide-react";

export function Hero() {
  return (
    <section className="relative pt-24 pb-16 md:pt-32 md:pb-24 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-orange-50 -z-10" />
      <div className="absolute top-20 right-0 w-96 h-96 bg-purple-200 rounded-full blur-3xl opacity-20 -z-10" />
      <div className="absolute bottom-0 left-0 w-72 h-72 bg-orange-200 rounded-full blur-3xl opacity-20 -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left - Copy */}
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
              <Zap size={14} />
              API pronta para integração
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              Provador Virtual
              <span className="gradient-text block">com Inteligência Artificial</span>
            </h1>

            <p className="text-lg text-gray-600 max-w-lg">
              Integre ao seu e-commerce em minutos. Nossa IA analisa medidas corporais,
              tom de pele e recomenda o tamanho perfeito — reduzindo devoluções em até 40%.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="#demo"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition shadow-lg shadow-purple-200"
              >
                Testar a Demo
                <ArrowRight size={18} />
              </a>
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition"
              >
                <Play size={18} />
                Ver como funciona
              </a>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap gap-6 pt-4">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <TrendingDown size={16} className="text-green-500" />
                -40% devoluções
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <ShieldCheck size={16} className="text-blue-500" />
                LGPD compliant
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Zap size={16} className="text-orange-500" />
                {"<"}2s resposta
              </div>
            </div>
          </div>

          {/* Right - Visual */}
          <div className="relative">
            <div className="relative bg-gray-900 rounded-2xl p-6 shadow-2xl">
              {/* Fake terminal/API response */}
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
                <span className="ml-2 text-xs text-gray-400 font-mono">
                  POST /api/v1/analyze/fit
                </span>
              </div>
              <pre className="text-xs sm:text-sm text-green-400 font-mono overflow-x-auto">
{`{
  "measurements": {
    "shoulder_width_cm": 42.5,
    "bust_cm": 97.8,
    "hip_cm": 96.2,
    "pants_length_cm": 103.7
  },
  "skin_analysis": {
    "undertone": "quente",
    "color_name": "Pele média"
  },
  "fit_score": 8.5,
  "recommended_size": "M",
  "style_advice": "Caimento ideal..."
}`}
              </pre>
            </div>
            {/* Floating badge */}
            <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-lg p-3 border border-gray-100">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 font-bold">8.5</span>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-900">Fit Score</p>
                  <p className="text-xs text-gray-500">Caimento ideal</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
