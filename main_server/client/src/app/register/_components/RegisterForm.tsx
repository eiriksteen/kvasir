"use client";

import PublicHeader from "@/components/headers/PublicHeader";
import { registerUser } from "@/lib/auth";
import { USER_ROLES } from "@/types/auth";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { signIn, useSession } from "next-auth/react";
import Link from "next/link";

export default function RegisterForm() {
  const router = useRouter();
  const { data: session } = useSession();
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
      setSuccessMessage("Registration successful! You can now log in.");
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

  const handleGoogleSignUp = async () => {
    const result = await signIn("google", {
      redirect: false
    });

    if (result?.error) {
      console.error(result.error);
      setErrorMessage('Google sign-up failed: ' + result.error);
    } else if (result?.ok) {
      // Session will be loaded, then effect will handle redirect
      router.refresh();
    }
  };

  // Handle redirect based on session state
  useEffect(() => {
    if (session) {
      if (session.needsProfileCompletion) {
        router.push('/complete-profile');
      } else {
        router.push('/projects');
      }
    }
  }, [session, router]);

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
                    placeholder="Your organization or institution"
                  />
                  <p className="mt-1 text-sm text-gray-500 font-[family-name:var(--font-geist-sans)]">
                    e.g., University name, Company name, or Independent
                  </p>
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
                  <p className="mt-1 text-sm text-gray-500 font-[family-name:var(--font-geist-sans)]">
                    Select the option that best describes your current role
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isRegistering}
                  className="w-full py-3 px-6 border border-transparent text-base font-medium rounded-md text-white bg-[#000034] hover:bg-[#000044] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-[family-name:var(--font-geist-sans)]"
                >
                  {isRegistering ? "Creating Account..." : "Create Account"}
                </button>
              </form>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500 font-[family-name:var(--font-geist-sans)]">Or continue with</span>
                </div>
              </div>

              <button onClick={handleGoogleSignUp} type="button" className="gsi-material-button">
                <div className="gsi-material-button-state"></div>
                <div className="gsi-material-button-content-wrapper">
                  <div className="gsi-material-button-icon">
                    <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" xmlnsXlink="http://www.w3.org/1999/xlink" style={{display: 'block'}}>
                      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
                      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
                      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
                      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
                      <path fill="none" d="M0 0h48v48H0z"></path>
                    </svg>
                  </div>
                  <span className="gsi-material-button-contents">Sign up with Google</span>
                  <span style={{display: 'none'}}>Sign up with Google</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

