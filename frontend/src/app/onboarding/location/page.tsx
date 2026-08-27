"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useState } from "react";

const DEMO_LOCATIONS = [
    { id: "delhi", name: "New Delhi, Delhi", lat: 28.6139, lon: 77.2090 },
    { id: "mumbai", name: "Mumbai, Maharashtra", lat: 19.0760, lon: 72.8777 },
    { id: "bengaluru", name: "Bengaluru, Karnataka", lat: 12.9716, lon: 77.5946 },
    { id: "chennai", name: "Chennai, Tamil Nadu", lat: 13.0827, lon: 80.2707 },
    { id: "srinagar", name: "Srinagar, J&K", lat: 34.0837, lon: 74.7973 } // Useful for winter/snow personas
];

export default function LocationPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [acquiring, setAcquiring] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showManual, setShowManual] = useState(false);
    const [selectedCity, setSelectedCity] = useState(DEMO_LOCATIONS[0].id);

    if (loading) return null;
    if (!user) {
        router.push("/login");
        return null;
    }

    const handleAcquireLocation = () => {
        setAcquiring(true);
        setError(null);
        setShowManual(false);

        if (!navigator.geolocation) {
            setError("Geolocation is not supported by your browser.");
            setAcquiring(false);
            setShowManual(true);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Save to localStorage for demo purposes to persist the chosen lat/lon for API calls
                localStorage.setItem("mausam_lat", position.coords.latitude.toString());
                localStorage.setItem("mausam_lon", position.coords.longitude.toString());
                localStorage.setItem("mausam_city", "Current Location");
                router.push("/home");
            },
            (err) => {
                console.error(err);
                setError("Location access denied or unavailable. Please select a city manually.");
                setAcquiring(false);
                setShowManual(true);
            }
        );
    };

    const handleManualFallback = () => {
        const city = DEMO_LOCATIONS.find(c => c.id === selectedCity);
        if (city) {
            localStorage.setItem("mausam_lat", city.lat.toString());
            localStorage.setItem("mausam_lon", city.lon.toString());
            localStorage.setItem("mausam_city", city.name);
            router.push("/home");
        }
    };

    return (
        <main className="onboarding h-full flex flex-col items-center justify-center p-4">
            <div className="onboarding-card max-w-md w-full p-8 shadow-lg rounded-2xl bg-white border border-gray-100">
                <section className="onboarding-content text-center flex flex-col items-center">
                    <p className="eyebrow text-blue-600 font-extrabold text-[10px] tracking-widest mb-2">STEP 2 OF 2</p>
                    <div className="text-5xl mb-4 text-center">📍</div>
                    <h1 className="text-3xl font-extrabold mb-2 tracking-tight">Enable Location</h1>
                    <p className="onboarding-subtitle mb-8 text-gray-500">We need your location to dynamically adapt the homepage to your local weather.</p>

                    {error && <div className="mb-4 p-3 bg-red-100 text-red-700 text-sm font-semibold rounded-lg w-full text-left">{error}</div>}

                    <button
                        onClick={handleAcquireLocation}
                        disabled={acquiring}
                        className="primary-btn w-full bg-blue-600 text-white font-bold p-4 rounded-xl shadow-md hover:-translate-y-0.5 transition-all disabled:opacity-50 mb-4"
                    >
                        {acquiring ? "Acquiring..." : "Detect Current Location"}
                    </button>

                    {!showManual ? (
                        <button
                            onClick={() => setShowManual(true)}
                            className="text-sm font-bold text-gray-500 hover:text-black py-2 transition-colors cursor-pointer w-full text-center"
                        >
                            Enter location manually instead
                        </button>
                    ) : (
                        <div className="w-full mt-4 p-4 border border-gray-200 rounded-xl bg-gray-50 flex flex-col gap-3 text-left animate-in fade-in zoom-in-95 duration-200">
                            <label className="text-xs font-extrabold text-gray-600 uppercase tracking-widest">Select Demo Location</label>
                            <select
                                className="w-full p-3 rounded-lg border border-gray-300 font-medium outline-none text-gray-800 bg-white"
                                value={selectedCity}
                                onChange={(e) => setSelectedCity(e.target.value)}
                            >
                                {DEMO_LOCATIONS.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                            <button
                                onClick={handleManualFallback}
                                className="w-full bg-black text-white font-bold py-3 rounded-lg mt-2 hover:-translate-y-0.5 transition-all shadow-md"
                            >
                                Use Selected City
                            </button>
                        </div>
                    )}
                </section>
            </div>
        </main>
    );
}
