export const API_BASE = "http://localhost:8000"; // Assuming default FastAPI dev server

export interface PreferencesBody {
    device_id: string;
    personas: string[];
    health_flags: string[];
    saved_locations: Record<string, unknown>[];
}

export interface SignalRef {
    signal: string;
    value: number | string | null;
    source: string;
}

export interface WarningResponse {
    severity: string;
    type: string;
    text: string;
}

export interface CardResponse {
    card_id: string;
    title: string;
    priority: string;
    is_alert: boolean;
    value_summary: string;
    source: string;
    freshness_badge: string | null;
    explanation_ref: string;
}

export interface HomepageResponse {
    context_snapshot_id: string;
    generated_at: string;
    cards: CardResponse[];
    warnings_override: WarningResponse[];
    system_notice: string | null;
}

export const fetchHomepage = async (deviceId: string, lat: number, lon: number): Promise<HomepageResponse> => {
    const params = new URLSearchParams({
        device_id: deviceId,
        lat: lat.toString(),
        lon: lon.toString()
    });

    const res = await fetch(`${API_BASE}/homepage?${params.toString()}`);
    if (!res.ok) {
        throw new Error(`Failed to fetch homepage: ${res.status}`);
    }
    return res.json();
};

export const fetchPreferences = async (deviceId: string): Promise<PreferencesBody> => {
    const res = await fetch(`${API_BASE}/preferences?device_id=${deviceId}`);
    if (!res.ok) {
        throw new Error(`Failed to fetch preferences: ${res.status}`);
    }
    return res.json();
};

export const updatePreferences = async (body: PreferencesBody): Promise<void> => {
    const res = await fetch(`${API_BASE}/preferences`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        throw new Error(`Failed to update preferences: ${res.status}`);
    }
};

export interface ExplainResponse {
    text: string;
    signal_refs: Array<{ signal: string; value: string | number | null }>;
    score_components: Record<string, number>;
}

export const fetchExplanation = async (deviceId: string, explanationRef: string): Promise<ExplainResponse> => {
    const params = new URLSearchParams({
        device_id: deviceId,
        explanation_ref: explanationRef
    });

    const res = await fetch(`${API_BASE}/explain?${params.toString()}`);
    if (!res.ok) {
        throw new Error(`Failed to fetch explanation: ${res.status}`);
    }
    return res.json();
};
