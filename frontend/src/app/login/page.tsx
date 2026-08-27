"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "@/lib/firebase";

export default function LoginPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!loading && user) {
            router.push("/home");
        }
    }, [user, loading, router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        try {
            await signInWithEmailAndPassword(auth, email, password);
            router.push("/home");
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message || "Invalid email or password");
            } else {
                setError("Failed to login. Please try again.");
            }
        }
    };

    if (loading || user) return null;

    return (
        <main className="onboarding h-full flex items-center justify-center">
            <div className="onboarding-card max-w-md w-full p-8 mx-auto mt-10 shadow-lg rounded-2xl bg-white border border-gray-100">
                <div className="onboarding-brand flex items-center gap-3 mb-8">
                    <div className="brand-icon flex items-center justify-center w-10 h-10 rounded-lg bg-blue-600 text-white font-bold text-xl shadow-md">M</div>
                    <div>
                        <h2 className="font-extrabold tracking-wide uppercase text-sm">MAUSAM</h2>
                        <span className="text-xs text-gray-500">Personalized Weather</span>
                    </div>
                </div>

                <section className="onboarding-content">
                    <p className="eyebrow text-blue-600 font-extrabold text-[10px] tracking-widest mb-2">WELCOME BACK</p>
                    <h1 className="text-3xl font-extrabold mb-2 tracking-tight">Login to Mausam</h1>
                    <p className="onboarding-subtitle mb-8 text-gray-500">Sign in to access your personalized weather experience.</p>

                    {error && <div className="mb-4 text-red-600 text-sm font-semibold">{error}</div>}

                    <form onSubmit={handleLogin} className="flex flex-col gap-5">
                        <div className="form-group flex flex-col gap-2">
                            <label className="text-sm font-bold text-gray-700" htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="p-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-500 focus:bg-white transition-colors"
                            />
                        </div>

                        <div className="form-group flex flex-col gap-2">
                            <label className="text-sm font-bold text-gray-700" htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                placeholder="Your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="p-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:border-blue-500 focus:bg-white transition-colors"
                            />
                        </div>

                        <button type="submit" className="primary-btn mt-4 w-full bg-blue-600 text-white font-bold p-4 rounded-xl shadow-md hover:bg-blue-700 hover:-translate-y-0.5 transition-all">
                            Login →
                        </button>
                    </form>

                    <p className="mt-6 text-center text-sm text-gray-600">
                        Don&apos;t have an account?{" "}
                        <a href="/signup" className="text-blue-600 font-bold hover:underline">
                            Create one
                        </a>
                    </p>
                </section>
            </div>
        </main>
    );
}
