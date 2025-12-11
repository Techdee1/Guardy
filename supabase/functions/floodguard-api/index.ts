// project/supabase/functions/floodguard-api/index.ts
// Full Deno function with multilingual emails, OSRM routing for safe routes,
// nearest-shelter lookup, and saves language preference on subscription.
//
// IMPORTANT:
// - Set RESEND_API_KEY or SENDGRID_API_KEY in function environment to send emails.
// - Supabase URL / service role key also required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
//
// Author: FloodGuard integration patch
// Date: 2025-12-10
// --------------------------------------------------------------

import { createClient } from "npm:@supabase/supabase-js@2.57.4";

// CORS headers (public API for demo)
const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers":
        "Content-Type, Authorization, X-Client-Info, Apikey",
};

// -----------------------------
// TypeScript interfaces
// -----------------------------
interface EmergencyReport {
    name: string;
    latitude: number;
    longitude: number;
    type_of_need: string;
    comments: string;
    timestamp: string;
    voice_recording_url?: string;
    location_name?: string;
}

interface FloodEvent {
    location: string;
    latitude: number;
    longitude: number;
    severity: string; // 'low'|'medium'|'high'
    rainfall?: number;
    description?: string;
    timestamp: string;
    // optional: supply flood_geojson to show exact area on map
    flood_geojson?: any;
}

interface AlertSubscription {
    phone?: string;
    email?: string;
    latitude: number;
    longitude: number;
    location_name?: string;
    language?: string; // 'en'|'yo'|'ha'|'ig'
    is_active?: boolean;
}

// -----------------------------
// Utility functions
// -----------------------------

/**
 * Haversine formula — distance in kilometers between two coordinates
 */
function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 6371; // earth radius in km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

/**
 * Reverse geocode with Nominatim — returns a human-readable location name
 * Falls back to coordinates if reverse geocoding fails.
 */
async function reverseGeocode(lat: number, lon: number): Promise<string> {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
            { headers: { "User-Agent": "FloodGuard-Nigeria/1.0" } }
        );
        if (!response.ok) return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
        const data = await response.json();
        const address = data.address || {};
        const parts = [
            address.suburb || address.neighbourhood || address.hamlet,
            address.city || address.town || address.village,
            address.state,
        ].filter(Boolean);
        return parts.length > 0
            ? parts.join(", ")
            : `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    } catch (err) {
        console.error("Reverse geocoding error:", err);
        return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    }
}

// -----------------------------
// Email sending helper (SendGrid compatible)
// Keeps original function shape but prefers SENDGRID_API_KEY or RESEND_API_KEY
// -----------------------------
async function sendEmail(
    to: string,
    subject: string,
    html: string,
    apiKey?: string
) {
    // If apiKey not provided, try environment variables
    const key =
        apiKey ||
        Deno.env.get("RESEND_API_KEY") ||
        Deno.env.get("SENDGRID_API_KEY");
    if (!key) {
        console.log(
            "Email API key not configured. Email skipped:",
            to,
            subject
        );
        return { success: false, message: "Email API key not configured" };
    }

    // Use SendGrid API shape (works with SendGrid). If you want Resend or others, adapt accordingly.
    try {
        const payload = {
            personalizations: [{ to: [{ email: to }] }],
            from: {
                email: "floodguard.ng@gmail.com",
                name: "FloodGuard Nigeria",
            },
            subject,
            content: [{ type: "text/html", value: html }],
        };

        const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${key}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        // If SendGrid returns 202 Accepted -> success (no JSON)
        if (response.ok || response.status === 202) {
            return { success: true, message: "Email queued by provider" };
        } else {
            const txt = await response.text();
            console.error("Email provider error:", response.status, txt);
            return { success: false, message: txt };
        }
    } catch (err) {
        console.error("Failed to send email:", err);
        return { success: false, message: String(err) };
    }
}

// -----------------------------
// Multilingual translation helper (EN, YO, HA, IG)
// Keeps subject + safety HTML for each supported language.
// -----------------------------
function translateFloodAlert(
    language: string,
    data: {
        severityText: string;
        location: string;
        description: string;
        distance: string;
    }
) {
    const translations: Record<string, any> = {
        en: {
            subject: `🚨 Flood Alert: ${data.severityText} - ${data.location}`,
            safety: `
        <ul>
          <li>Avoid flooded areas and roads</li>
          <li>Move to higher ground immediately</li>
          <li>Keep emergency contacts ready</li>
        </ul>
      `,
        },
        yo: {
            subject: `🚨 Ìkìlọ̀ Òjò: ${data.severityText} - ${data.location}`,
            safety: `
        <ul>
          <li>Má lọ sí àwọn ibi tí omi ti kun</li>
          <li>Gbé s'òkè tàbí ibi tí ó ga</li>
          <li>Pa àwọn nọ́mbà pajawiri mọ́ra</li>
        </ul>
      `,
        },
        ha: {
            subject: `🚨 Gargadin Ambaliya: ${data.severityText} - ${data.location}`,
            safety: `
        <ul>
          <li>Guji wuraren da ambaliya ta shafa</li>
          <li>Hayi zuwa wuri mafi tsawo</li>
          <li>Kasance da lambobin gaggawa a shirye</li>
        </ul>
      `,
        },
        ig: {
            subject: `🚨 Ọnwụ Mmiri: ${data.severityText} - ${data.location}`,
            safety: `
        <ul>
          <li>Zere ebe mmiri juru</li>
          <li>Gawa ebe dị elu ozugbo</li>
          <li>Debe nọmba gbaghara n'akụkụ gị</li>
        </ul>
      `,
        },
    };

    return translations[language] || translations["en"];
}

// -----------------------------
// Routing helper using public OSRM server
// Returns an object with geometry (geojson LineString), distance (meters), duration (seconds)
// Note: OSRM public server is free but rate-limited; use with care.
// -----------------------------
async function getSafeRoute(
    fromLat: number,
    fromLon: number,
    toLat: number,
    toLon: number
) {
    try {
        const url = `https://router.project-osrm.org/route/v1/driving/${fromLon},${fromLat};${toLon},${toLat}?overview=full&geometries=geojson&annotations=duration,distance`;
        const r = await fetch(url);
        if (!r.ok) {
            console.warn("OSRM request failed:", await r.text());
            return null;
        }
        const json = await r.json();
        const route = json.routes?.[0];
        if (!route) return null;
        return {
            geometry: route.geometry,
            distance: route.distance,
            duration: route.duration,
        };
    } catch (err) {
        console.error("getSafeRoute error:", err);
        return null;
    }
}

// -----------------------------
// Deno server (main)
// -----------------------------
Deno.serve(async (req: Request) => {
    // Early OPTIONS CORS response
    if (req.method === "OPTIONS") {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        // Base URL path handling (your function expects routes under /floodguard-api/)
        const url = new URL(req.url);
        const path = url.pathname
            .replace("/floodguard-api/", "")
            .replace(/^\/+/, "");

        // Initialize Supabase client using service role key (server-side)
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        if (!supabaseUrl || !supabaseKey) {
            console.error("Missing Supabase env variables");
            return new Response(
                JSON.stringify({
                    success: false,
                    message: "Server config error",
                }),
                {
                    status: 500,
                    headers: {
                        ...corsHeaders,
                        "Content-Type": "application/json",
                    },
                }
            );
        }
        const supabase = createClient(supabaseUrl, supabaseKey);

        // Email API key env var
        const emailApiKey =
            Deno.env.get("RESEND_API_KEY") || Deno.env.get("SENDGRID_API_KEY");

        // -------------------------
        // GET /floods — list recent flood events
        // -------------------------
        if (path === "floods" && req.method === "GET") {
            const { data, error } = await supabase
                .from("flood_events")
                .select("*")
                .order("timestamp", { ascending: false })
                .limit(100);

            if (error) throw error;

            return new Response(JSON.stringify({ success: true, data }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // POST /floods — create a flood event, notify nearby subscribers
        // returns nearestShelters + routes in the response for frontend mapping
        // -------------------------
        if (path === "floods" && req.method === "POST") {
            const floodEvent: FloodEvent = await req.json();

            // Insert flood event row
            const { data, error } = await supabase
                .from("flood_events")
                .insert([floodEvent])
                .select();

            if (error) throw error;
            const insertedEvent = data[0];

            // Fetch active subscribers
            const { data: subscribers, error: subscribersError } =
                await supabase
                    .from("alert_subscriptions")
                    .select("*")
                    .eq("is_active", true);

            if (subscribersError) {
                console.error("Failed to fetch subscribers:", subscribersError);
            }

            // Fetch emergency centers (shelters) to compute nearest shelters
            const { data: centers, error: centersError } = await supabase
                .from("emergency_centers")
                .select("*");

            if (centersError) {
                console.error(
                    "Failed to fetch emergency centers:",
                    centersError
                );
            }

            // Compute nearest shelters (top 3)
            const nearestShelters = (centers || [])
                .map((center: any) => ({
                    ...center,
                    distance: calculateDistance(
                        Number(insertedEvent.latitude),
                        Number(insertedEvent.longitude),
                        Number(center.latitude),
                        Number(center.longitude)
                    ),
                }))
                .sort((a: any, b: any) => a.distance - b.distance)
                .slice(0, 3);

            // Compute OSRM routes from event location to each shelter (sequentially)
            // Note: doing this sequentially avoids overloading the OSRM public server.
            const routes: any[] = [];
            for (const sh of nearestShelters) {
                const route = await getSafeRoute(
                    Number(insertedEvent.latitude),
                    Number(insertedEvent.longitude),
                    Number(sh.latitude),
                    Number(sh.longitude)
                );
                routes.push({
                    shelter: {
                        id: sh.id,
                        name: sh.name,
                        latitude: sh.latitude,
                        longitude: sh.longitude,
                        distance_km: sh.distance,
                    },
                    route, // may be null if routing failed
                });
            }

            // Now notify nearby subscribers (within 20 km) via email using their preferred language
            let notificationsSent = 0;
            if (subscribers && subscribers.length > 0 && emailApiKey) {
                const nearbySubscribers = (subscribers || [])
                    .map((sub: any) => ({
                        ...sub,
                        distance: calculateDistance(
                            Number(insertedEvent.latitude),
                            Number(insertedEvent.longitude),
                            Number(sub.latitude),
                            Number(sub.longitude)
                        ),
                    }))
                    .filter((sub: any) => sub.distance <= 20 && sub.email); // only email-enabled nearby subs

                const severityColor =
                    insertedEvent.severity === "high"
                        ? "#dc2626"
                        : insertedEvent.severity === "medium"
                        ? "#f59e0b"
                        : "#3b82f6";
                const severityText =
                    insertedEvent.severity === "high"
                        ? "HIGH SEVERITY"
                        : insertedEvent.severity === "medium"
                        ? "MEDIUM"
                        : "LOW";

                // Build and send emails (parallel send but limited by system)
                const emailPromises = nearbySubscribers.map((sub: any) => {
                    const preferredLang =
                        sub.language &&
                        ["en", "yo", "ha", "ig"].includes(sub.language)
                            ? sub.language
                            : "en";
                    const translated = translateFloodAlert(preferredLang, {
                        severityText,
                        location: insertedEvent.location,
                        description: insertedEvent.description || "",
                        distance: `${sub.distance.toFixed(1)} km`,
                    });

                    // HTML email template (simple and safe). Keep insertedEvent.description sanitized if it's user-provided.
                    const html = `
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"/></head>
            <body style="font-family: Arial, sans-serif; color: #111;">
              <div style="max-width: 700px; margin:0 auto; padding: 12px;">
                <div style="background:${severityColor}; color:#fff; padding:12px; border-radius:6px;">
                  <h2 style="margin:0">${translated.subject}</h2>
                </div>

                <div style="background:#fff; padding:12px; border:1px solid #eee; border-radius:6px; margin-top:8px;">
                  <p><strong>Location:</strong> ${insertedEvent.location}</p>
                  <p>${
                      insertedEvent.description
                          ? insertedEvent.description
                          : "Flood conditions detected in your area."
                  }</p>
                  <p><strong>Distance from you:</strong> ${sub.distance.toFixed(
                      1
                  )} km</p>

                  <h3>Safety Recommendations</h3>
                  ${translated.safety}

                  <hr/>

                  <p><strong>Nearest shelters:</strong></p>
                  <ul>
                    ${nearestShelters
                        .map(
                            (s) =>
                                `<li>${s.name} — ${s.distance.toFixed(
                                    1
                                )} km</li>`
                        )
                        .join("")}
                  </ul>

                  <p style="font-size:12px; color:#666;">You received this because you registered for flood alerts at <strong>${
                      sub.location_name || "your location"
                  }</strong>.</p>
                </div>

                <p style="font-size:12px; color:#888; text-align:center; margin-top:8px;">FloodGuard Nigeria</p>
              </div>
            </body>
            </html>
          `;

                    return sendEmail(
                        sub.email,
                        translated.subject,
                        html,
                        emailApiKey
                    );
                });

                const results = await Promise.all(emailPromises);
                notificationsSent = results.filter(
                    (r: any) => r?.success
                ).length;
            } else {
                if (!emailApiKey) {
                    console.log(
                        "Email API key not configured; skipping emails."
                    );
                }
            }

            // Finally respond including nearest shelters + routes so the frontend can display map + arrows
            return new Response(
                JSON.stringify({
                    success: true,
                    data,
                    nearestShelters,
                    routes,
                    notificationsSent,
                    totalSubscribers: subscribers?.length || 0,
                }),
                {
                    headers: {
                        ...corsHeaders,
                        "Content-Type": "application/json",
                    },
                }
            );
        }

        // -------------------------
        // GET /reports - list emergency reports
        // -------------------------
        if (path === "reports" && req.method === "GET") {
            const { data, error } = await supabase
                .from("emergency_reports")
                .select("*")
                .order("timestamp", { ascending: false })
                .limit(100);

            if (error) throw error;

            return new Response(JSON.stringify({ success: true, data }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // POST /reports - receive emergency report + notify nearby centers
        // (kept almost identical to your original implementation)
        // -------------------------
        if (path === "reports" && req.method === "POST") {
            const report: EmergencyReport = await req.json();

            const locationName = await reverseGeocode(
                report.latitude,
                report.longitude
            );
            const reportWithLocation = {
                ...report,
                location_name: locationName,
            };

            const { data: insertedReport, error: insertError } = await supabase
                .from("emergency_reports")
                .insert([reportWithLocation])
                .select()
                .single();

            if (insertError) throw insertError;

            // Find nearby centers and notify them by email
            const { data: centers, error: centersError } = await supabase
                .from("emergency_centers")
                .select("*");

            if (centersError) throw centersError;

            const nearbyCenters = (centers || [])
                .map((center: any) => ({
                    ...center,
                    distance: calculateDistance(
                        report.latitude,
                        report.longitude,
                        Number(center.latitude),
                        Number(center.longitude)
                    ),
                }))
                .filter((c: any) => c.distance <= 10)
                .sort((a: any, b: any) => a.distance - b.distance)
                .slice(0, 3);

            const emailPromises = nearbyCenters.map((center: any) => {
                const html = `
          <!DOCTYPE html>
          <html><head><meta charset="utf-8"/></head>
          <body style="font-family: Arial, sans-serif;">
            <div style="max-width:700px;margin:0 auto;padding:12px;">
              <div style="background:#dc2626;color:#fff;padding:12px;border-radius:6px;">
                <h2 style="margin:0">🚨 Emergency Report</h2>
              </div>
              <div style="background:#fff;padding:12px;border:1px solid #eee;border-radius:6px;margin-top:8px;">
                <p><strong>Name:</strong> ${report.name}</p>
                <p><strong>Need:</strong> ${report.type_of_need}</p>
                <p><strong>Location:</strong> ${locationName}</p>
                <p>Coords: ${report.latitude.toFixed(
                    4
                )}, ${report.longitude.toFixed(4)}</p>
                <p><strong>Distance:</strong> ${nearbyCenters
                    .find((c: any) => c.id === center.id)
                    ?.distance.toFixed(2)} km</p>
                <p>${report.comments || "No additional comments"}</p>
              </div>
            </div>
          </body></html>
        `;
                return sendEmail(
                    center.email,
                    `🚨 Emergency Report: ${report.type_of_need}`,
                    html,
                    emailApiKey
                );
            });

            const emailResults = await Promise.all(emailPromises);

            return new Response(
                JSON.stringify({
                    success: true,
                    data: insertedReport,
                    nearbyCenters,
                    notifications: emailResults,
                }),
                {
                    headers: {
                        ...corsHeaders,
                        "Content-Type": "application/json",
                    },
                }
            );
        }

        // -------------------------
        // PUT /reports - update report status
        // -------------------------
        if (path === "reports" && req.method === "PUT") {
            const { id, status } = await req.json();

            const { data, error } = await supabase
                .from("emergency_reports")
                .update({ status })
                .eq("id", id)
                .select();

            if (error) throw error;

            return new Response(JSON.stringify({ success: true, data }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // GET /centers - list emergency centers (shelters)
        // -------------------------
        if (path === "centers" && req.method === "GET") {
            const { data, error } = await supabase
                .from("emergency_centers")
                .select("*");

            if (error) throw error;
            return new Response(JSON.stringify({ success: true, data }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // GET /weather - proxy to OpenWeatherMap (unchanged)
        // -------------------------
        if (path === "weather" && req.method === "GET") {
            const city = url.searchParams.get("city");
            const lat = url.searchParams.get("lat");
            const lon = url.searchParams.get("lon");
            const apiKey =
                url.searchParams.get("apiKey") ||
                Deno.env.get("OPENWEATHER_API_KEY") ||
                "53b1e8acf21399ed870cbe9fec7aa0b5";

            let weatherUrl = "";
            if (lat && lon) {
                weatherUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`;
            } else {
                const cityName = city || "Lagos";
                weatherUrl = `https://api.openweathermap.org/data/2.5/weather?q=${cityName},NG&appid=${apiKey}&units=metric`;
            }

            const weatherResponse = await fetch(weatherUrl);
            if (!weatherResponse.ok)
                throw new Error("Failed to fetch weather data");
            const weatherData = await weatherResponse.json();

            return new Response(
                JSON.stringify({ success: true, data: weatherData }),
                {
                    headers: {
                        ...corsHeaders,
                        "Content-Type": "application/json",
                    },
                }
            );
        }

        // -------------------------
        // GET /flood-forecast - proxy to open-meteo flood API (unchanged)
        // -------------------------
        if (path === "flood-forecast" && req.method === "GET") {
            const lat = url.searchParams.get("lat");
            const lon = url.searchParams.get("lon");

            if (!lat || !lon) {
                return new Response(
                    JSON.stringify({
                        success: false,
                        message: "Latitude and longitude are required",
                    }),
                    {
                        status: 400,
                        headers: {
                            ...corsHeaders,
                            "Content-Type": "application/json",
                        },
                    }
                );
            }

            const floodUrl = `https://flood-api.open-meteo.com/v1/flood?latitude=${lat}&longitude=${lon}&daily=river_discharge,river_discharge_mean,river_discharge_max,river_discharge_min&forecast_days=7`;
            const floodResponse = await fetch(floodUrl);
            if (!floodResponse.ok)
                throw new Error("Failed to fetch flood forecast data");
            const floodData = await floodResponse.json();

            return new Response(
                JSON.stringify({ success: true, data: floodData }),
                {
                    headers: {
                        ...corsHeaders,
                        "Content-Type": "application/json",
                    },
                }
            );
        }

        // -------------------------
        // POST /alerts/register - register (or update) alert subscription
        // Accepts { email?, phone?, latitude, longitude, location_name?, language? }
        // -------------------------
        if (path === "alerts/register" && req.method === "POST") {
            const subscription: AlertSubscription = await req.json();

            // validate
            if (
                (!subscription.email && !subscription.phone) ||
                subscription.latitude == null ||
                subscription.longitude == null
            ) {
                return new Response(
                    JSON.stringify({
                        success: false,
                        message:
                            "Email or phone, latitude, and longitude are required",
                    }),
                    {
                        status: 400,
                        headers: {
                            ...corsHeaders,
                            "Content-Type": "application/json",
                        },
                    }
                );
            }

            const locationName =
                subscription.location_name ||
                (await reverseGeocode(
                    subscription.latitude,
                    subscription.longitude
                ));

            const contactField = subscription.email ? "email" : "phone";
            const contactValue = subscription.email || subscription.phone;

            // check existing subscription
            const { data: existingSubscription, error: checkError } =
                await supabase
                    .from("alert_subscriptions")
                    .select("*")
                    .eq(contactField, contactValue)
                    .maybeSingle();

            if (checkError) throw checkError;

            let result;
            if (existingSubscription) {
                // update existing
                const { data, error } = await supabase
                    .from("alert_subscriptions")
                    .update({
                        email: subscription.email,
                        phone: subscription.phone,
                        latitude: subscription.latitude,
                        longitude: subscription.longitude,
                        location_name: locationName,
                        is_active: true,
                        language: subscription.language || "en",
                    })
                    .eq(contactField, contactValue)
                    .select()
                    .single();

                if (error) throw error;
                result = {
                    data,
                    message: "Alert subscription updated successfully",
                };
            } else {
                // create new
                const { data, error } = await supabase
                    .from("alert_subscriptions")
                    .insert([
                        {
                            email: subscription.email,
                            phone: subscription.phone,
                            latitude: subscription.latitude,
                            longitude: subscription.longitude,
                            location_name: locationName,
                            language: subscription.language || "en",
                        },
                    ])
                    .select()
                    .single();

                if (error) throw error;

                // send confirmation email if possible
                if (emailApiKey && subscription.email) {
                    const html = `
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"/></head>
            <body style="font-family: Arial, sans-serif;">
              <div style="max-width:700px;margin:0 auto;padding:12px;">
                <div style="background:#3b82f6;color:#fff;padding:12px;border-radius:6px;text-align:center;">
                  <h2 style="margin:0">🛡️ FloodGuard Nigeria</h2>
                </div>
                <div style="background:#fff;padding:12px;border:1px solid #eee;border-radius:6px;margin-top:8px;">
                  <p>You have successfully registered for flood alerts.</p>
                  <p><strong>Your Location:</strong> ${locationName}</p>
                  <p><strong>Preferred language:</strong> ${
                      subscription.language || "en"
                  }</p>
                </div>
                <p style="font-size:12px;color:#666;text-align:center;">FloodGuard Nigeria</p>
              </div>
            </body>
            </html>
          `;
                    await sendEmail(
                        subscription.email,
                        "🛡️ FloodGuard Alert Registration Confirmed",
                        html,
                        emailApiKey
                    );
                }

                result = {
                    data,
                    message: "Alert subscription created successfully",
                };
            }

            return new Response(JSON.stringify({ success: true, ...result }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // GET /alerts/check?email=... or ?phone=... - check subscription
        // -------------------------
        if (path === "alerts/check" && req.method === "GET") {
            const email = url.searchParams.get("email");
            const phone = url.searchParams.get("phone");

            if (!email && !phone) {
                return new Response(
                    JSON.stringify({
                        success: false,
                        message: "Email or phone number is required",
                    }),
                    {
                        status: 400,
                        headers: {
                            ...corsHeaders,
                            "Content-Type": "application/json",
                        },
                    }
                );
            }

            let query = supabase.from("alert_subscriptions").select("*");
            query = email ? query.eq("email", email) : query.eq("phone", phone);

            const { data, error } = await query.maybeSingle();
            if (error) throw error;

            return new Response(JSON.stringify({ success: true, data }), {
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            });
        }

        // -------------------------
        // Not found
        // -------------------------
        return new Response(
            JSON.stringify({ success: false, message: "Not found" }),
            {
                status: 404,
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            }
        );
    } catch (error) {
        console.error("Error:", error);
        return new Response(
            JSON.stringify({ success: false, message: String(error) }),
            {
                status: 500,
                headers: { ...corsHeaders, "Content-Type": "application/json" },
            }
        );
    }
});
