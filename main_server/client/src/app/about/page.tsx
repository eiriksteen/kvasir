import Link from "next/link";
import Image from "next/image";
import PublicHeader from "@/components/headers/PublicHeader";

export default function AboutPage() {
  const founders = [
    {
      name: "Eirik Drage Steen",
      role: "Co-Founder & CEO",
      bio: "Eirik has worked as a data scientist at CERN and Deutsche Bank. He holds a Msc in Engineering from the Norwegian University of Science and Technology (NTNU). Eirik also spent one academic year at Berkeley, where he studied Computer Science and Machine Learning. He is currently pursuing a PhD in Data Science at the University of Virginia.",
      expertise: ["Machine Learning", "Data Science", "Product Vision"],
      linkedin: "https://www.linkedin.com/in/eirik-drage-steen-0771061b6/",
      image: "/eirik_headshot.jpeg"
    },
    {
      name: "Sondre Rogde",
      role: "Co-Founder & CTO",
      bio: "Sondre has worked as experience from banking and as a data scientist at Norges Bank Investment Management (NBIM). He holds a Msc in Engineering from the Norwegian University of Science and Technology (NTNU). Sondre also spent one academic year at Harvard, where he studied Computer Science and Machine Learning. He is currently pursuing an Msc in Mathematical and Computational Engineering at Stanford University.",
      expertise: ["Machine Learning", "Data Science", "Product Vision"],
      linkedin: "https://www.linkedin.com/in/sondre-rogde-86717a1b8/",
      image: "/sondre_headshot.jpeg"
    }
  ];

  return (
    <>
    <PublicHeader />
    <div className="min-h-screen bg-white pt-20 pb-16">
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    {/* Hero Section */}
    <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-[#000034] mb-4 font-[family-name:var(--font-geist-sans)]">
        About Kvasir
        </h1>
        <div className="max-w-3xl mx-auto">
          <p className="text-lg text-gray-600 mb-4 font-[family-name:var(--font-geist-sans)] text-center">
            Kvasir is an AI-powered platform covering every step of the data science journey:
          </p>
          <ul className="list-none p-0 flex flex-row gap-6 justify-center">
            <li className="flex items-center text-gray-700 font-[family-name:var(--font-geist-sans)]">
              <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 6.293a1 1 0 00-1.414 0L9 12.586l-2.293-2.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l7-7a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
              </svg>
              Data Cleaning
            </li>
            <li className="flex items-center text-gray-700 font-[family-name:var(--font-geist-sans)]">
              <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 6.293a1 1 0 00-1.414 0L9 12.586l-2.293-2.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l7-7a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
              </svg>
              Data Structuring
            </li>
            <li className="flex items-center text-gray-700 font-[family-name:var(--font-geist-sans)]">
              <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 6.293a1 1 0 00-1.414 0L9 12.586l-2.293-2.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l7-7a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
              </svg>
              Analysis
            </li>
            <li className="flex items-center text-gray-700 font-[family-name:var(--font-geist-sans)]">
              <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 6.293a1 1 0 00-1.414 0L9 12.586l-2.293-2.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l7-7a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
              </svg>
              Modeling
            </li>
            <li className="flex items-center text-gray-700 font-[family-name:var(--font-geist-sans)]">
              <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 6.293a1 1 0 00-1.414 0L9 12.586l-2.293-2.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l7-7a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
              </svg>
              Deployment
            </li>
          </ul>
        </div>
    </div>


    {/* Founders Section */}
    <div className="mb-16">
        <h2 className="text-3xl font-bold text-[#000034] mb-12 text-center font-[family-name:var(--font-geist-sans)]">
        Meet Our Founders
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
        {founders.map((founder, index) => (
            <div
            key={index}
            className="border border-gray-200 rounded-lg p-8 bg-white hover:shadow-lg transition-shadow duration-200"
            >
            {/* Profile Image Placeholder */}
            <div className="mb-6">
                <div className="w-32 h-32 mx-auto bg-gradient-to-br from-[#000034] to-gray-600 rounded-full flex items-center justify-center">
                {/* <span className="text-white text-4xl font-bold font-[family-name:var(--font-geist-sans)]">
                    {founder.name.split(' ').map(n => n[0]).join('')}
                </span> */}
                <Image
                    src={founder.image}
                    alt={founder.name}
                    width={128}
                    height={128}
                    className="rounded-full"
                />
                </div>
            </div>

            <div className="text-center mb-4">
                <h3 className="text-2xl font-semibold text-[#000034] mb-2 font-[family-name:var(--font-geist-sans)]">
                {founder.name}
                </h3>
                <p className="text-[#000034] font-medium mb-4 font-[family-name:var(--font-geist-sans)]">
                {founder.role}
                </p>
            </div>

            <p className="text-gray-600 mb-6 text-center font-[family-name:var(--font-geist-sans)]">
                {founder.bio}
            </p>

            <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2 text-center font-[family-name:var(--font-geist-sans)]">
                Expertise
                </h4>
                <div className="flex flex-wrap justify-center gap-2">
                {founder.expertise.map((skill, skillIndex) => (
                    <span
                    key={skillIndex}
                    className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full font-[family-name:var(--font-geist-sans)]"
                    >
                    {skill}
                    </span>
                ))}
                </div>
            </div>

            <div className="flex justify-center mt-6">
                <a
                href={founder.linkedin}
                className="text-[#000034] hover:text-gray-600 transition-colors"
                aria-label="LinkedIn"
                >
                <svg
                    className="h-6 w-6"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                </svg>
                </a>
            </div>
            </div>
        ))}
        </div>
    </div>

    {/* Story Section */}
    <div className="mb-16">
        <h2 className="text-3xl font-bold text-[#000034] mb-12 text-center font-[family-name:var(--font-geist-sans)]">
        Our Story
        </h2>
        <p className="text-gray-600 mb-6 text-center font-[family-name:var(--font-geist-sans)]">
            We met at NTNU in 2020 but it wasn&apos;t until 2023 when we started ReLU NTNU together that we started working closely together. ReLU NTNU is a student organization that does ML and AI projects in collaboration with industry partners. After a year we had sourced projects from 7 major Norwegian companies, recruited 30+ members, and achieved 50k USD in revenue.
            During these projects we saw that much of our work could be automated with the right tools. However, the available tools lacked the sophistication to handle the complexity of real-world data science projects. We therefore started working on Kvasir, a tool for data scientists tailored to the complexities of industry projects.
            {/* Projects we worked on included: */}
        </p>
        {/* <div className="flex justify-center">
            <ul className="list-disc text-gray-600 mb-6 text-left mx-auto">
                <li className="mb-2">Anomaly detection in energy consumption data</li>
                <li className="mb-2">Prediction of appetite for caged salmon</li>
                <li className="mb-2">Aneurism detection in medical images</li>
                <li className="mb-2">Caption generation for news images</li>
                <li className="mb-2">Demand forecasting using alternative data sources</li>
            </ul>
        </div> */}
    </div>

    {/* CTA Section */}
    <div className="text-center bg-gradient-to-r from-[#000034] to-gray-800 rounded-lg p-12">
        <h2 className="text-3xl font-bold text-white mb-4 font-[family-name:var(--font-geist-sans)]">
        Sign up Now for Early Access
        </h2>
        <p className="text-gray-200 mb-8 max-w-2xl mx-auto font-[family-name:var(--font-geist-sans)]">
        Limited spots available. Sign up for the waitlist to be notified when we launch.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
            href="/login"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-[#000034] bg-white hover:bg-gray-100 transition-colors duration-200"
        >
            Get Started
        </Link>
        <Link
            href="/waitlist"
            className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-base font-medium rounded-md text-white hover:bg-white hover:text-[#000034] transition-colors duration-200"
        >
            Join the Waitlist
        </Link>
        </div>
    </div>
    </div>
</div>
</>
  );
}
