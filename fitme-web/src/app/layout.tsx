import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FITME - Provador Virtual com IA | API para E-commerce",
  description:
    "Integre um provador virtual inteligente ao seu e-commerce. Análise corporal por IA, recomendação de tamanho e consultoria de estilo em tempo real.",
  keywords: [
    "provador virtual",
    "IA",
    "e-commerce",
    "recomendação de tamanho",
    "visão computacional",
    "moda",
    "API",
  ],
  openGraph: {
    title: "FITME - Provador Virtual com IA",
    description: "Reduza devoluções em 40%. API de provador virtual para e-commerce.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
