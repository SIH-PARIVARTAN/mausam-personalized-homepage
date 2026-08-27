"use client";

import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Topbar() {
    const { user, loading, logout } = useAuth();
    const router = useRouter();
    const [city, setCity] = useState("Loading location...");

    useEffect(() => {
        if (!loading && user) {
            const storedCity = localStorage.getItem("mausam_city");
            if (storedCity) {
                setCity(storedCity);
            } else if (localStorage.getItem("mausam_lat")) {
                setCity("Current Location");
            } else {
                setCity("Location Unknown");
            }
        }
    }, [user, loading]);

    if (loading) return null;

    return (
        <header className="topbar">
            <div className="brand cursor-pointer" onClick={() => router.push("/")}>
                <div className="brand-icon">M</div>
                <div>
                    <h2>MAUSAM</h2>
                    <span>Personalized Weather</span>
                </div>
            </div>

            {user && (
                <>
                    <div className="location">
                        <span className="opacity-70">📍</span>
                        <span id="user-location" className="font-bold">{city}</span>
                    </div>

                    <div className="profile cursor-pointer" onClick={logout} title="Click to logout">
                        <div className="profile-avatar">
                            {user.displayName ? user.displayName.charAt(0).toUpperCase() : "M"}
                        </div>
                    </div>
                </>
            )}
        </header>
    );
}
