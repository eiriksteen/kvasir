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
            router.push('/dashboard');
        }
    };
    
    return (
        <div>
        <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
            <Image
            src="/miyawtext.png"
            alt="miya logo"
            width={180}
            height={38}
            priority
            />
            <div className="bg-[rgb(104,16,255)] p-8 rounded-xl w-full max-w-sm">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
                <input
                type="email"
                name="email"
                placeholder="Email"
                className="w-full px-4 py-2 rounded-lg bg-black text-white"
                required
                />
                <input
                type="password"
                name="password"
                placeholder="Password"
                className="w-full px-4 py-2 rounded-lg bg-black text-white"
                required
                />
                <button 
                type="submit"
                className="bg-black text-white rounded-lg hover:bg-black/70 px-4 py-2 mt-2"
                >
                Sign In
                </button>
            </form>
            </div>
        </main>
        </div>
    );
} 