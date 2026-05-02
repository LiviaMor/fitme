"use client";

import { Check } from "lucide-react";

const plans = [
  {
    name: "Starter",
    price: "Grátis",
    period: "até 100 análises/mês",
    description: "Para testar e validar a integração",
    features: [
      "100 análises/mês",
      "API REST completa",
      "Medidas corporais",
      "Tom de pele",
      "Suporte por email",
    ],
    cta: "Começar Grátis",
    highlighted: false,
  },
  {
    name: "Growth",
    price: "R$ 297",
    period: "/mês",
    description: "Para e-commerces em crescimento",
    features: [
      "5.000 análises/mês",
      "Consultoria de estilo com IA",
      "Recomendação de tamanho",
      "Estadiômetro digital Welmy",
      "Webhook de eventos",
      "Dashboard analytics",
      "Suporte prioritário",
    ],
    cta: "Assinar Growth",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Sob consulta",
    period: "",
    description: "Para grandes operações",
    features: [
      "Análises ilimitadas",
      "Modelo de IA customizado",
      "White-label completo",
      "SLA 99.9%",
      "Integração dedicada",
      "Account manager",
      "On-premise disponível",
    ],
    cta: "Falar com Vendas",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Planos que escalam com você
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Comece grátis, escale conforme cresce. Sem surpresas.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 ${
                plan.highlighted
                  ? "bg-purple-600 text-white shadow-xl shadow-purple-200 scale-105"
                  : "bg-white border border-gray-200"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-orange-400 text-white text-xs font-bold rounded-full">
                  MAIS POPULAR
                </div>
              )}

              <h3
                className={`text-lg font-semibold mb-1 ${
                  plan.highlighted ? "text-white" : "text-gray-900"
                }`}
              >
                {plan.name}
              </h3>
              <p
                className={`text-sm mb-4 ${
                  plan.highlighted ? "text-purple-200" : "text-gray-500"
                }`}
              >
                {plan.description}
              </p>

              <div className="mb-6">
                <span className="text-3xl font-bold">{plan.price}</span>
                <span
                  className={`text-sm ${
                    plan.highlighted ? "text-purple-200" : "text-gray-500"
                  }`}
                >
                  {plan.period}
                </span>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check
                      size={16}
                      className={`mt-0.5 flex-shrink-0 ${
                        plan.highlighted ? "text-purple-200" : "text-green-500"
                      }`}
                    />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-3 rounded-xl font-medium transition ${
                  plan.highlighted
                    ? "bg-white text-purple-600 hover:bg-gray-100"
                    : "bg-purple-600 text-white hover:bg-purple-700"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
