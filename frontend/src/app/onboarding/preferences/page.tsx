"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { updatePreferences } from "@/lib/api";

const AVAILABLE_PERSONAS = [
    { id: "health", icon: "♥", label: "Health (Demo)" },
    { id: "fitness", icon: "🏃", label: "Fitness (Demo)" },
    { id: "family", icon: "👨‍👩‍👧", label: "Family (Demo)" },
    { id: "beach", icon: "🏖️", label: "Beach (Coming Soon)", disabled: true },
    { id: "travel", icon: "✈", label: "Travel (Coming Soon)", disabled: true },
    { id: "agriculture", icon: "🌱", label: "Agriculture (Coming Soon)", disabled: true },
    { id: "commute", icon: "🚗", label: "Commute (Coming Soon)", disabled: true },
    { id: "events", icon: "💍", label: "Events (Coming Soon)", disabled: true },
];

export default function PreferencesPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (loading) return null;
    if (!user) {
        router.push("/login");
        return null;
    }

    const togglePersona = (id: string, disabled: boolean = false) => {
        if (disabled) return;
        setSelectedPersonas(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const handleSave = async () => {
        setSubmitting(true);
        setError(null);

        try {
            await updatePreferences({
                device_id: user.uid,
                personas: selectedPersonas,
                health_flags: [],
                saved_locations: []
            });
            // Skip location onboarding for now or route to it
            router.push("/onboarding/location");
        } catch (err: unknown) {
            console.error(err instanceof Error ? err.message : err);
            setError((err instanceof Error ? err.message : "An unknown error occurred") || "Failed to save preferences.");
            setSubmitting(false);
        }
    };

    return (
        <main className="onboarding h-full flex flex-col items-center justify-center p-4">
            <div className="onboarding-card max-w-2xl w-full p-8 shadow-lg rounded-2xl bg-white border border-gray-100">
                <section className="onboarding-content">
                    <p className="eyebrow text-blue-600 font-extrabold text-[10px] tracking-widest mb-2">STEP 1 OF 2</p>
                    <h1 className="text-3xl font-extrabold mb-2 tracking-tight">What matters to you?</h1>
                    <p className="onboarding-subtitle mb-8 text-gray-500">Select the topics you care about to personalize your weather experience.</p>

                    {error && <div className="mb-4 text-red-600 text-sm font-semibold">{error}</div>}

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                        {AVAILABLE_PERSONAS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => togglePersona(p.id, p.disabled)}
                                className={`p-4 border rounded-xl flex flex-col items-center gap-2 transition-all ${p.disabled
                                    ? "opacity-50 cursor-not-allowed bg-gray-50"
                                    : selectedPersonas.includes(p.id)
                                        ? "border-black bg-black text-white"
                                        : "border-gray-200 hover:border-gray-300"
                                    }`}
                            >
                                <span className="text-2xl">{p.icon}</span>
                                <span className="text-xs font-bold text-center">{p.label}</span>
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={submitting}
                        className="primary-btn w-full bg-blue-600 text-white font-bold p-4 rounded-xl shadow-md hover:bg-blue-700 hover:-translate-y-0.5 transition-all disabled:opacity-50"
                    >
                        {submitting ? "Saving..." : "Continue →"}
                    </button>
                </section>
            </div>
        </main>
    );
}
