import Image from "next/image";
import TypedHeading from "@/components/TypedHeading";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/getSession";


export default async function Home() {

  const session = await getSession();

  if (session && !session?.error) {
    redirect("/projects");
  }

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)] bg-white">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
        <Image
          src="/kvasirwtext.png"
          alt="kvasir logo"
          width={180}
          height={38}
          priority
        />
        <TypedHeading
          strings={[
            "Agents for all your data.",
          ]}
          typeSpeed={0.0001}
          loop={false}
          className="text-center sm:text-left font-[family-name:var(--font-geist-mono)] text-gray-800"
        />
      </main>
    </div>
  );
}
