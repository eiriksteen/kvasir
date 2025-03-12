'use client';

import Image from "next/image";
import { ReactTyped } from "react-typed";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
        <Image
          src="/miya.png"
          alt="miya logo"
          width={180}
          height={38}
          priority
        />
        <ReactTyped
          strings={[
            "Your AI Engineer Agent.",
          ]}
          typeSpeed={3}
          backSpeed={5}
          loop={false}
          className="text-center sm:text-left font-[family-name:var(--font-geist-mono)]"
        />
        <button 
          className="bg-black text-white rounded-lg hover:bg-gray-800"
          onClick={() => window.location.href = '/dashboard'}
        >
          Get Started
        </button>
      </main>
    </div>
  );
}
