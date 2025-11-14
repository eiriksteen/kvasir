"use client";

import PublicHeader from "@/components/headers/PublicHeader";
import { registerUser } from "@/lib/auth";
import { USER_ROLES } from "@/types/auth";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [isRegistering, setIsRegistering] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    affiliation: "",
    role: ""
  });
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    setErrorMessage("");

    // Validate password match
    if (formData.password !== formData.confirmPassword) {
      setErrorMessage("Passwords do not match");
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long");
      return;
    }

    setIsRegistering(true);
    try {
      await registerUser({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        affiliation: formData.affiliation,
        role: formData.role,
        disabled: false
      });
      setSuccessMessage("Registration successful! Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to register");
    } finally {
      setIsRegistering(false);
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
              Create Your Account
            </h1>
            <p className="text-gray-600 font-[family-name:var(--font-geist-sans)]">
              Already have an account?{" "}
              <Link href="/login" className="text-[#000034] hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
            {/* Registration Form */}
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
                    Name *
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
                    Email *
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
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                    Password *
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength={8}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                    placeholder="At least 8 characters"
                  />
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                    Confirm Password *
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    minLength={8}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#000034] focus:border-transparent outline-none transition-colors font-[family-name:var(--font-geist-sans)]"
                    placeholder="Confirm your password"
                  />
                </div>

                <div>
                  <label htmlFor="affiliation" className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]">
                    Affiliation *
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
                    Role *
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
                    {USER_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isRegistering}
                  className="w-full py-3 px-6 border border-transparent text-base font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-[family-name:var(--font-geist-sans)]"
                >
                  {isRegistering ? "Creating Account..." : "Create Account"}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

