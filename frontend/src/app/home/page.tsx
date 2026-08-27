"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchHomepage, updatePreferences, fetchPreferences } from "@/lib/api";

import ExplainDrawer from "@/components/ExplainDrawer";

const ICON_MAP: Record<string, string> = {
    "severe_warning": "🚨",
    "aqi_health": "😷",
    "uv_sun_exposure": "☀️",
    "activity_window": "🏃",
    "rain_commute": "🚗",
    "sunrise_sunset": "🌅",
    "general_conditions": "☁️",
    "pollen_illustrative": "🌱"
};

const COLOR_MAP: Record<string, string> = {
    P0: "bg-red-50 text-red-700 border-red-200",
    P1: "bg-orange-50 text-orange-700 border-orange-200",
    P2: "bg-blue-50 text-blue-700 border-blue-300",
    P3: "bg-white text-gray-800 border-gray-200",
    P4: "bg-gray-50 text-gray-400 border-gray-200"
};

const cleanText = (text: string) => {
    if (!text) return "";
    return text.replace(/\(shown as a low-priority.*?\)/gi, "").trim();
};

export default function HomePage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const queryClient = useQueryClient();

    const [lat, setLat] = useState<number | null>(null);
    const [lon, setLon] = useState<number | null>(null);
    const [selectedExplainRef, setSelectedExplainRef] = useState<string | null>(null);

    const checkedPrefs = useRef(false);

    useEffect(() => {
        if (loading) return;
        if (!user) {
            router.push("/login");
            return;
        }

        const verifyFlow = async () => {
            if (checkedPrefs.current) return;

            try {
                const prefs = await fetchPreferences(user.uid);
                if (prefs.personas.length === 1 && prefs.personas[0] === "default_general") {
                    router.push("/onboarding/preferences");
                    return;
                }
                checkedPrefs.current = true;

                const savedLat = localStorage.getItem("mausam_lat");
                const savedLon = localStorage.getItem("mausam_lon");
                if (savedLat && savedLon) {
                    setLat(parseFloat(savedLat));
                    setLon(parseFloat(savedLon));
                } else {
                    router.push("/onboarding/location");
                }
            } catch (err) {
                console.error("Failed to verify onboarding state", err);
            }
        };

        verifyFlow();
    }, [user, loading, router]);

    const { data: prefData } = useQuery({
        queryKey: ["preferences", user?.uid],
        queryFn: () => fetchPreferences(user!.uid),
        enabled: !!user,
    });

    const activePersona = prefData?.personas?.[0] || "";

    const { data, isLoading, isError, isFetching } = useQuery({
        queryKey: ["homepage", user?.uid, lat, lon],
        queryFn: () => fetchHomepage(user!.uid, lat!, lon!),
        enabled: !!user && lat !== null && lon !== null,
    });

    const mutation = useMutation({
        mutationFn: async (personas: string[]) => {
            await updatePreferences({
                device_id: user!.uid,
                personas,
                health_flags: [],
                saved_locations: []
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["preferences"] });
            queryClient.invalidateQueries({ queryKey: ["homepage"] });
        }
    });

    const handlePersonaChange = (personaId: string) => {
        if (activePersona === personaId) return;
        mutation.mutate([personaId]);
    };

    if (loading || !user) return null;

    const topCard = data?.cards?.[0];
    const subCards = data?.cards?.slice(1) || [];

    return (
        <main className="container mx-auto px-4 py-8 md:py-12 max-w-6xl relative">
            <section className="hero flex flex-col md:flex-row md:justify-between md:items-end mb-10 gap-4">
                <div>
                    <p className="eyebrow text-blue-600 font-extrabold text-[10px] sm:text-xs tracking-widest mb-2 uppercase">Personalized for you</p>
                    <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900">
                        Good afternoon, <span className="text-blue-600">{user.displayName || "User"}.</span>
                    </h1>
                    <p className="hero-subtitle text-gray-500 mt-2 text-sm sm:text-base lg:text-lg max-w-xl">
                        Here's what matters to you today.
                    </p>
                </div>
                <button
                    className="settings-btn px-5 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-bold text-gray-700 shadow-sm hover:shadow-md hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                    onClick={() => router.push("/onboarding/preferences")}
                >
                    ⚙️ Settings
                </button>
            </section>

            {/* Basic Persona Toggles */}
            <section className="persona-section flex gap-3 overflow-x-auto pb-4 mb-8 scrollbar-hide">
                {["health", "fitness", "family"].map((persona) => {
                    const isActive = activePersona === persona;
                    return (
                        <button
                            key={persona}
                            onClick={() => handlePersonaChange(persona)}
                            className={`px-6 py-2.5 border rounded-full font-bold text-sm sm:text-base whitespace-nowrap transition-all flex items-center justify-center ${isActive ? 'bg-blue-600 text-white border-blue-600 shadow-md transform scale-[1.02]' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50 cursor-pointer'}`}
                        >
                            {persona.charAt(0).toUpperCase() + persona.slice(1)}
                        </button>
                    );
                })}
                <button className="px-6 py-2.5 border border-dashed border-gray-300 bg-gray-50 text-gray-400 rounded-full font-bold text-sm sm:text-base whitespace-nowrap cursor-not-allowed opacity-60">
                    Travel (Soon)
                </button>
            </section>

            {isError && (
                <div className="p-5 bg-red-100 text-red-800 rounded-xl font-bold mb-6 border border-red-200 shadow-sm">
                    Error fetching personalized weather data.
                </div>
            )}

            {(isLoading || isFetching) && !data && (
                <div className="flex flex-col items-center justify-center p-16 gap-4">
                    <div className="animate-spin text-5xl">🌀</div>
                    <p className="text-gray-500 font-medium">Gathering your personalized insights...</p>
                </div>
            )}

            {/* Warnings & System Notices */}
            {data?.system_notice && (
                <div className="p-5 bg-yellow-100 text-yellow-800 rounded-xl font-bold mb-6 shadow-sm border border-yellow-200">
                    {data.system_notice}
                </div>
            )}

            {data?.warnings_override && data.warnings_override.map((w, idx) => (
                <div key={idx} className="p-6 bg-red-600 text-white rounded-2xl font-bold mb-8 shadow-lg shadow-red-600/20 border border-red-700">
                    <div className="text-xl sm:text-2xl mb-2 flex items-center gap-2">🚨 <span className="uppercase tracking-wide">{w.type} WARNING</span></div>
                    <p className="font-medium text-red-100 text-lg leading-relaxed">{cleanText(w.text)}</p>
                </div>
            ))}

            {/* Render the Backend Sequential Cards */}
            {topCard && (
                <div className="recommendations mt-4">
                    <h2 className="text-xs font-extrabold text-blue-600 uppercase tracking-widest mb-4">Top Priority Today</h2>

                    {/* Rank 1 Feature Card */}
                    <div
                        onClick={() => setSelectedExplainRef(topCard.explanation_ref)}
                        className={`cursor-pointer w-full p-6 sm:p-8 rounded-3xl border flex flex-col md:flex-row items-start md:items-center gap-6 transition-all hover:-translate-y-1 hover:shadow-xl shadow-sm mb-10 ${COLOR_MAP[topCard.priority] || COLOR_MAP.P3}`}
                    >
                        <div className="text-5xl sm:text-6xl w-20 h-20 sm:w-24 sm:h-24 flex items-center justify-center bg-white/70 rounded-2xl shadow-sm flex-shrink-0">
                            {ICON_MAP[topCard.card_id] || "⚪"}
                        </div>
                        <div className="flex-1">
                            <div className="flex flex-wrap gap-2 items-center mb-3">
                                <span className="text-[10px] font-black px-3 py-1 bg-white/90 shadow-sm rounded-lg text-gray-800 tracking-wider">RANK 1</span>
                                {topCard.freshness_badge && (
                                    <span className="px-3 py-1 text-[10px] sm:text-xs font-bold uppercase tracking-wider bg-black/10 rounded-lg text-gray-800">
                                        {topCard.freshness_badge}
                                    </span>
                                )}
                            </div>
                            <h3 className="font-extrabold text-2xl sm:text-3xl mb-3 tracking-tight text-gray-900">{topCard.title}</h3>
                            <p className="text-base sm:text-lg opacity-90 leading-relaxed font-semibold mb-4 max-w-3xl text-gray-800">
                                {cleanText(topCard.value_summary)}
                            </p>
                            <span className="inline-flex items-center text-sm font-extrabold text-blue-700 bg-white/90 px-4 py-2 rounded-xl border border-white/50 transition-colors shadow-sm">
                                Why this matters →
                            </span>
                        </div>
                    </div>

                    {subCards.length > 0 && (
                        <>
                            <h2 className="text-xs font-extrabold text-gray-400 uppercase tracking-widest mb-4">Secondary Insights</h2>

                            {/* Sub Grid (Cards 2-5) */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                                {subCards.map((card, index) => (
                                    <div
                                        key={card.card_id}
                                        onClick={() => setSelectedExplainRef(card.explanation_ref)}
                                        className={`cursor-pointer p-6 rounded-2xl border flex flex-col items-start gap-4 transition-all hover:scale-[1.02] hover:-translate-y-1 hover:shadow-lg shadow-sm h-full ${COLOR_MAP[card.priority] || COLOR_MAP.P3}`}
                                    >
                                        <div className="flex justify-between items-start w-full">
                                            <div className="text-3xl w-14 h-14 flex items-center justify-center bg-white/70 rounded-xl shadow-sm">
                                                {ICON_MAP[card.card_id] || "⚪"}
                                            </div>
                                            <span className="text-[9px] font-black tracking-wider px-3 py-1 bg-white/90 shadow-sm rounded-lg text-gray-700">RANK {index + 2}</span>
                                        </div>

                                        <div className="flex-1 flex flex-col justify-start w-full mt-2">
                                            <h3 className="font-extrabold text-xl leading-tight mb-2 tracking-tight text-gray-900">{card.title}</h3>
                                            <p className="text-sm opacity-[0.85] leading-relaxed font-semibold mb-4 line-clamp-3 text-gray-800">
                                                {cleanText(card.value_summary)}
                                            </p>
                                        </div>

                                        <div className="mt-auto w-full flex justify-between items-center border-t border-black/10 pt-4">
                                            <span className="text-[11px] text-blue-700 font-extrabold uppercase tracking-widest bg-white/50 px-2 py-1 rounded">
                                                View insight →
                                            </span>
                                            {card.freshness_badge && (
                                                <span className="text-[9px] font-bold uppercase overflow-hidden text-ellipsis bg-black/10 px-2 py-1 rounded text-gray-700">
                                                    {card.freshness_badge}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            )}

            <ExplainDrawer
                deviceId={user.uid}
                explanationRef={selectedExplainRef}
                onClose={() => setSelectedExplainRef(null)}
            />
        </main>
    );
}
