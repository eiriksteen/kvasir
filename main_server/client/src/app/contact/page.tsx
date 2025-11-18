import Link from "next/link";
import PublicHeader from "@/components/headers/PublicHeader";

export default function ContactPage() {
  return (
    <>
    <PublicHeader />
      <div className="min-h-screen bg-white pt-20 pb-16">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-[#000034] mb-4 font-[family-name:var(--font-geist-sans)]">
            Get in Touch
          </h1>
          <p className="text-lg text-gray-600 font-[family-name:var(--font-geist-sans)]">
            Have questions? We&apos;d love to hear from you. Send us a message and we&apos;ll respond as soon as possible.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Form */}
          <div className="border border-gray-200 rounded-lg p-8 bg-white">
            <h2 className="text-2xl font-semibold text-[#000034] mb-6 font-[family-name:var(--font-geist-sans)]">
              Send us a message
            </h2>
            <form className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                  placeholder="Your name"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                  placeholder="your.email@example.com"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Affiliation
                </label>
                <input
                  type="text"
                  id="affiliation"
                  name="affiliation"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                  placeholder="Your affiliation"
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Role
                </label>
                <select
                  id="role"
                  name="role"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                >
                  <option value="">Select your role</option>
                  <option value="student">Student</option>
                  <option value="non-technical">Non-technical</option>
                  <option value="researcher">Researcher</option>
                  <option value="data-scientist">Data scientist</option>
                  <option value="data-engineer">Data engineer</option>
                  <option value="ml-engineer">ML engineer</option>
                  <option value="ml-ops">ML ops</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Subject
                </label>
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                  placeholder="How can we help?"
                />
              </div>

              <div>
                <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Message
                </label>
                <textarea
                  id="message"
                  name="message"
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors resize-none font-[family-name:var(--font-geist-sans)]"
                  placeholder="Tell us more about your inquiry..."
                />
              </div>

              <button
                type="submit"
                className="w-full py-3 px-6 border border-transparent text-base font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] transition-colors duration-200 font-[family-name:var(--font-geist-sans)]"
              >
                Send Message
              </button>
            </form>
          </div>

          {/* Contact Information */}
          <div className="space-y-8">
            <div className="border border-gray-200 rounded-lg p-8 bg-white">
              <h2 className="text-2xl font-semibold text-[#000034] mb-6 font-[family-name:var(--font-geist-sans)]">
                Contact Information
              </h2>
              
              <div className="space-y-6">
                <div className="flex items-start">
                  <svg
                    className="h-6 w-6 text-[#000034] mr-4 mt-1 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1 font-[family-name:var(--font-geist-sans)]">Email</h3>
                    <p className="text-gray-600 font-[family-name:var(--font-geist-sans)]">contact@kvasir.ai</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <svg
                    className="h-6 w-6 text-[#000034] mr-4 mt-1 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1 font-[family-name:var(--font-geist-sans)]">Office</h3>
                    <p className="text-gray-600 font-[family-name:var(--font-geist-sans)]">
                      Coming soon
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <svg
                    className="h-6 w-6 text-[#000034] mr-4 mt-1 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1 font-[family-name:var(--font-geist-sans)]">Business Hours</h3>
                    <p className="text-gray-600 font-[family-name:var(--font-geist-sans)]">
                      Monday - Friday: 9:00 AM - 6:00 PM
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-8 bg-gray-50">
              <h3 className="text-lg font-semibold text-[#000034] mb-3 font-[family-name:var(--font-geist-sans)]">
                Quick Start
              </h3>
              <p className="text-gray-600 mb-4 font-[family-name:var(--font-geist-sans)]">
                Want to start using Kvasir right away?
              </p>
              <Link
                href="/login"
                className="inline-flex items-center justify-center px-6 py-2 border border-[#000034] text-sm font-medium rounded-md text-[#000034] bg-white hover:bg-[#000034] hover:text-white transition-colors duration-200"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
