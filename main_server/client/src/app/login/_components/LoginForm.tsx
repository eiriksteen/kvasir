'use client';

import Image from "next/image";
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';


export default function LoginForm() {
    const router = useRouter();

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
            router.push('/projects');
        }
    };
    
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
            </div>
        </main>
        </div>
    );
} 