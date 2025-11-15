"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import PublicHeader from "@/components/headers/PublicHeader";
import { USER_ROLES } from "@/types/auth";
import { camelToSnakeKeys } from "@/lib/utils";

export default function CompleteProfileForm() {
  const router = useRouter();
  const { data: session, update } = useSession();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    affiliation: "",
    role: ""
  });
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!formData.affiliation || !formData.role) {
      setErrorMessage("Please fill in all fields");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/update-profile`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session?.APIToken?.accessToken}`,
          },
          body: JSON.stringify(camelToSnakeKeys(formData)),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: "Failed to update profile",
        }));
        throw new Error(errorData.detail || `Failed to update profile: ${response.status}`);
      }

      // Update the session to clear the needsProfileCompletion flag
      await update();

      // Redirect to projects
      router.push("/projects");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <>
      <PublicHeader />
      <div className="min-h-screen bg-white pt-20 pb-16">
        <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-[#000034] mb-4 font-[family-name:var(--font-geist-sans)]">
              Complete Your Profile
            </h1>
            <p className="text-gray-600 font-[family-name:var(--font-geist-sans)]">
              Please provide some additional information to get started
            </p>
          </div>

          {/* Form */}
          <div className="border border-gray-200 rounded-lg p-8 bg-white">
            {errorMessage && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
                {errorMessage}
              </div>
            )}

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="affiliation"
                  className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]"
                >
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
                  placeholder="Your organization or institution"
                />
                <p className="mt-1 text-sm text-gray-500 font-[family-name:var(--font-geist-sans)]">
                  e.g., University name, Company name, or Independent
                </p>
              </div>

              <div>
                <label
                  htmlFor="role"
                  className="block text-sm font-medium text-gray-700 mb-2 font-[family-name:var(--font-geist-sans)]"
                >
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
                      {role
                        .split("-")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" ")}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-sm text-gray-500 font-[family-name:var(--font-geist-sans)]">
                  Select the option that best describes your current role
                </p>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 px-6 border border-transparent text-base font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-[family-name:var(--font-geist-sans)]"
              >
                {isSubmitting ? "Saving..." : "Complete Profile"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

