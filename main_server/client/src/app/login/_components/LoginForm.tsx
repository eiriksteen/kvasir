'use client';

import Image from "next/image";
import { signIn, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';


export default function LoginForm() {
    const router = useRouter();
    const { data: session } = useSession();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const email = formData.get('email') as string;
        const password = formData.get('password') as string;

        const result = await signIn("credentials", {
            email: email,
            password: password,
            redirect: false
        });

        if (result?.error) {
            console.error(result.error);
            alert('Login failed: ' + result.error);
        } else {
            // Redirect will be handled by middleware if profile completion is needed
            router.push('/projects');
        }
    };

    const handleGoogleSignIn = async () => {
        const result = await signIn("google", {
            redirect: false
        });

        if (result?.error) {
            console.log("We get something here")
            console.error(result.error);
            alert('Google sign-in failed: ' + result.error);
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
        <div>
        <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
            <Image
            src="/kvasirwtext.png"
            alt="kvasir logo"
            width={180}
            height={38}
            priority
            />
            <div className="bg-gray-100 p-8 rounded-xl w-full max-w-sm border border-gray-200">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
                <input
                type="email"
                name="email"
                placeholder="Email"
                className="w-full px-4 py-2 rounded-lg bg-white border border-gray-300 text-gray-800 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#000034] focus:border-[#000034] transition-colors"
                required
                />
                <input
                type="password"
                name="password"
                placeholder="Password"
                className="w-full px-4 py-2 rounded-lg bg-white border border-gray-300 text-gray-800 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#000034] focus:border-[#000034] transition-colors"
                required
                />
                <button
                type="submit"
                className="bg-[#000034] text-white rounded-lg hover:bg-[#000028] px-4 py-2 mt-2 transition-colors border border-[#000034]"
                >
                Sign In
                </button>
            </form>
            
            <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-gray-100 text-gray-500">Or continue with</span>
                </div>
            </div>

            <button onClick={handleGoogleSignIn} type="button" className="gsi-material-button">
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
                    <span className="gsi-material-button-contents">Sign in with Google</span>
                    <span style={{display: 'none'}}>Sign in with Google</span>
                </div>
                </button>
            </div>
        </main>
        </div>
    );
} 