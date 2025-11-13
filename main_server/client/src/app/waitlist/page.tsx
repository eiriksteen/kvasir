"use client";

import PublicHeader from "@/components/headers/PublicHeader";
import { useWaitlist } from "@/hooks/waitlist";
import { useState } from "react";

export default function WaitlistPage() {
  const { joinWaitlist, isJoining } = useWaitlist();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    affiliation: "",
    role: ""
  });
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    setErrorMessage("");

    try {
      await joinWaitlist(formData);
      setSuccessMessage("Successfully joined the waitlist! We'll be in touch soon.");
      setFormData({ name: "", email: "", affiliation: "", role: "" });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to join waitlist");
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <>
    <PublicHeader />
      <div className="min-h-screen bg-white pt-20 pb-16">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-[#000034] mb-4 font-[family-name:var(--font-geist-sans)]">
            Join the Waitlist
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
          {/* Contact Form */}
          <div className="border border-gray-200 rounded-lg p-8 bg-white">
            {successMessage && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md text-green-800">
                {successMessage}
              </div>
            )}
            
            {errorMessage && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
                {errorMessage}
              </div>
            )}

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
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
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                  placeholder="your.email@example.com"
                />
              </div>

              <div>
                <label htmlFor="affiliation" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                  Affiliation
                </label>
                <input
                  type="text"
                  id="affiliation"
                  name="affiliation"
                  value={formData.affiliation}
                  onChange={handleChange}
                  required
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
                  value={formData.role}
                  onChange={handleChange}
                  required
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

              <button
                type="submit"
                disabled={isJoining}
                className="w-full py-3 px-6 border border-transparent text-base font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-[family-name:var(--font-geist-sans)]"
              >
                {isJoining ? "Joining..." : "Join Waitlist"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
