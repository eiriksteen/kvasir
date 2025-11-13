import Link from "next/link";
import PublicHeader from "@/components/headers/PublicHeader";

export default function ProductsPage() {

  return (
    <>
    <PublicHeader />
      <div className="min-h-screen bg-white pt-20 pb-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">

        {/* Pricing Tiers Section */}
        <div className="mb-16">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-[#000034] mb-4 font-[family-name:var(--font-geist-sans)]">
              Pricing Plans
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto font-[family-name:var(--font-geist-sans)]">
              Choose the plan that&apos;s right for you and your team
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Simple Tier */}
            <div className="border border-gray-200 rounded-lg p-6 bg-white hover:shadow-lg transition-shadow duration-200">
              <h3 className="text-xl font-semibold text-[#000034] mb-2 font-[family-name:var(--font-geist-sans)]">
                Simple
              </h3>
              <div className="mb-4">
                <span className="text-3xl font-bold text-[#000034] font-[family-name:var(--font-geist-sans)]">Free</span>
              </div>
              <p className="text-gray-600 text-sm mb-6 font-[family-name:var(--font-geist-sans)]">
                Perfect for individuals getting started
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Up to 3 projects
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Basic analytics
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  1GB storage
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Community support
                </li>
              </ul>
              <Link
                href="/login"
                className="block text-center w-full py-2 px-4 border border-[#000034] text-sm font-medium rounded-md text-[#000034] bg-white hover:bg-[#000034] hover:text-white transition-colors duration-200"
              >
                Get Started
              </Link>
            </div>

            {/* Advanced Tier */}
            <div className="border border-gray-200 rounded-lg p-6 bg-white hover:shadow-lg transition-shadow duration-200">
              <h3 className="text-xl font-semibold text-[#000034] mb-2 font-[family-name:var(--font-geist-sans)]">
                Advanced
              </h3>
              <div className="mb-4">
                <span className="text-3xl font-bold text-[#000034] font-[family-name:var(--font-geist-sans)]">$49</span>
                <span className="text-gray-600 text-sm font-[family-name:var(--font-geist-sans)]">/month</span>
              </div>
              <p className="text-gray-600 text-sm mb-6 font-[family-name:var(--font-geist-sans)]">
                For professionals and small teams
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Up to 15 projects
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Advanced analytics
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  50GB storage
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Priority support
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  API access
                </li>
              </ul>
              <Link
                href="/login"
                className="block text-center w-full py-2 px-4 border border-[#000034] text-sm font-medium rounded-md text-[#000034] bg-white hover:bg-[#000034] hover:text-white transition-colors duration-200"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Tier */}
            <div className="border-2 border-[#000034] rounded-lg p-6 bg-white shadow-lg relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-[#000034] text-white px-3 py-1 text-xs font-semibold rounded-full font-[family-name:var(--font-geist-sans)]">
                  POPULAR
                </span>
              </div>
              <h3 className="text-xl font-semibold text-[#000034] mb-2 font-[family-name:var(--font-geist-sans)]">
                Pro
              </h3>
              <div className="mb-4">
                <span className="text-3xl font-bold text-[#000034] font-[family-name:var(--font-geist-sans)]">$149</span>
                <span className="text-gray-600 text-sm font-[family-name:var(--font-geist-sans)]">/month</span>
              </div>
              <p className="text-gray-600 text-sm mb-6 font-[family-name:var(--font-geist-sans)]">
                For growing teams and businesses
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Unlimited projects
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Premium analytics
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  500GB storage
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  24/7 dedicated support
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Advanced API access
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Custom integrations
                </li>
              </ul>
              <Link
                href="/login"
                className="block text-center w-full py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] transition-colors duration-200"
              >
                Get Started
              </Link>
            </div>

            {/* Enterprise Tier */}
            <div className="border border-gray-200 rounded-lg p-6 bg-white hover:shadow-lg transition-shadow duration-200">
              <h3 className="text-xl font-semibold text-[#000034] mb-2 font-[family-name:var(--font-geist-sans)]">
                Enterprise
              </h3>
              <div className="mb-4">
                <span className="text-3xl font-bold text-[#000034] font-[family-name:var(--font-geist-sans)]">Custom</span>
              </div>
              <p className="text-gray-600 text-sm mb-6 font-[family-name:var(--font-geist-sans)]">
                For large organizations with specific needs
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Unlimited everything
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Enterprise analytics
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Custom storage
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Dedicated account manager
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  SLA guarantees
                </li>
                <li className="flex items-start text-sm text-gray-700 font-[family-name:var(--font-geist-sans)]">
                  <svg className="h-5 w-5 text-[#000034] mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  On-premise deployment
                </li>
              </ul>
              <Link
                href="/contact"
                className="block text-center w-full py-2 px-4 border border-[#000034] text-sm font-medium rounded-md text-[#000034] bg-white hover:bg-[#000034] hover:text-white transition-colors duration-200"
              >
                Contact Sales
              </Link>
            </div>
          </div>
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
