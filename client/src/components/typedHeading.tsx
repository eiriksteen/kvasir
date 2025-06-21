"use client";

import { ReactTyped } from "react-typed";

interface TypedHeadingProps {
  strings: string[];
  typeSpeed?: number;
  loop?: boolean;
  className?: string;
}
    
export default function TypedHeading({ strings, typeSpeed = 0.0001, loop = false }: TypedHeadingProps) {

  return (
    <ReactTyped
        strings={strings}
        typeSpeed={typeSpeed}
        loop={loop}
        className="text-center sm:text-left font-[family-name:var(--font-geist-mono)]"
    />
  );
}
