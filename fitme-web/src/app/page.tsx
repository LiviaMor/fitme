import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { HowItWorks } from "@/components/HowItWorks";
import { Scanner360 } from "@/components/Scanner360";
import { TryOn } from "@/components/TryOn";
import { Demo } from "@/components/Demo";
import { Pricing } from "@/components/Pricing";
import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Scanner360 />
      <TryOn />
      <Demo />
      <Pricing />
      <Footer />
    </main>
  );
}
