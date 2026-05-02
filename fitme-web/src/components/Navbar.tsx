"use client";

import { useState } from "react";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
              <span className="text-white font-bold text-sm">F</span>
            </div>
            <span className="text-xl font-bold text-gray-900">FITME</span>
          </div>

          {/* Desktop */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-gray-600 hover:text-purple-600 transition">
              Recursos
            </a>
            <a href="#how-it-works" className="text-sm text-gray-600 hover:text-purple-600 transition">
              Como Funciona
            </a>
            <a href="#demo" className="text-sm text-gray-600 hover:text-purple-600 transition">
              Demo
            </a>
            <a href="#tryon" className="text-sm text-gray-600 hover:text-purple-600 transition">
              Provador
            </a>
            <a href="#pricing" className="text-sm text-gray-600 hover:text-purple-600 transition">
              Planos
            </a>
            <a
              href="#demo"
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition"
            >
              Testar Grátis
            </a>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Menu"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile menu */}
        {isOpen && (
          <div className="md:hidden pb-4 border-t border-gray-100 mt-2 pt-4">
            <div className="flex flex-col gap-3">
              <a href="#features" className="text-gray-600 hover:text-purple-600 py-2">Recursos</a>
              <a href="#how-it-works" className="text-gray-600 hover:text-purple-600 py-2">Como Funciona</a>
              <a href="#demo" className="text-gray-600 hover:text-purple-600 py-2">Demo</a>
              <a href="#pricing" className="text-gray-600 hover:text-purple-600 py-2">Planos</a>
              <a
                href="#demo"
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg text-center"
              >
                Testar Grátis
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
