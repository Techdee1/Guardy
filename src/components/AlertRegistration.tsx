// project/src/components/AlertRegistration.tsx
// React component for registering a user for alerts with preferred language
// Replace your existing component with this (keeps geolocation, posts to alerts/register)

import React, { useState } from "react";

export default function AlertRegistration() {
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [latitude, setLatitude] = useState<number | null>(null);
    const [longitude, setLongitude] = useState<number | null>(null);
    const [locationName, setLocationName] = useState("");
    const [language, setLanguage] = useState<"en" | "yo" | "ha" | "ig">("en");
    const [message, setMessage] = useState("");

    const useMyLocation = () => {
        if (!navigator.geolocation) {
            setMessage("Geolocation not supported in this browser.");
            return;
        }
        setMessage("Requesting your location...");
        navigator.geolocation.getCurrentPosition(
            (p) => {
                setLatitude(Number(p.coords.latitude));
                setLongitude(Number(p.coords.longitude));
                setMessage("Location acquired — please submit the form.");
            },
            (err) => {
                setMessage("Could not get location: " + err.message);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage("");
        if ((!email && !phone) || latitude == null || longitude == null) {
            setMessage(
                "Please provide email or phone and allow location access."
            );
            return;
        }

        const payload: any = {
            email: email || null,
            phone: phone || null,
            latitude,
            longitude,
            location_name: locationName || undefined,
            language,
        };

        try {
            // Adjust path if your function is mounted elsewhere
            const res = await fetch("/floodguard-api/alerts/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const json = await res.json();
            if (json.success) {
                setMessage(
                    "Registration successful — you will receive alerts in your selected language."
                );
                // Clear form if desired
            } else {
                setMessage(
                    "Registration failed: " + (json.message || "unknown error")
                );
            }
        } catch (err) {
            setMessage("Request failed: " + String(err));
        }
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="space-y-4 p-4 max-w-md mx-auto"
        >
            <div>
                <label className="block text-sm font-medium">Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="mt-1 block w-full p-2 border rounded"
                    placeholder="you@example.com"
                />
            </div>

            <div>
                <label className="block text-sm font-medium">Phone</label>
                <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="mt-1 block w-full p-2 border rounded"
                    placeholder="+234..."
                />
            </div>

            <div>
                <label className="block text-sm font-medium">
                    Preferred Alert Language
                </label>
                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as any)}
                    className="mt-1 block w-full p-2 border rounded"
                >
                    <option value="en">English</option>
                    <option value="yo">Yorùbá</option>
                    <option value="ha">Hausa</option>
                    <option value="ig">Igbo</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium">
                    Location name (optional)
                </label>
                <input
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    className="mt-1 block w-full p-2 border rounded"
                    placeholder="Eg. Ajegunle"
                />
            </div>

            <div className="flex items-center gap-2">
                <button
                    type="button"
                    onClick={useMyLocation}
                    className="px-4 py-2 bg-blue-500 text-white rounded"
                >
                    Use my current location
                </button>
                <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 text-white rounded"
                >
                    Register for Alerts
                </button>
            </div>

            {message && <p className="text-sm mt-2">{message}</p>}
        </form>
    );
}
