"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchExplanation } from "@/lib/api";

interface ExplainDrawerProps {
    deviceId: string;
    explanationRef: string | null;
    onClose: () => void;
}

export default function ExplainDrawer({ deviceId, explanationRef, onClose }: ExplainDrawerProps) {
    const { data, isLoading, isError } = useQuery({
        queryKey: ["explanation", deviceId, explanationRef],
        queryFn: () => fetchExplanation(deviceId, explanationRef!),
        enabled: !!explanationRef && !!deviceId,
    });

    if (!explanationRef) return null;

    return (
        <>
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity"
                onClick={onClose}
            />
            <div className="fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-3xl shadow-2xl p-6 sm:p-10 transition-transform transform translate-y-0 max-h-[85vh] overflow-y-auto w-full max-w-2xl mx-auto border-t border-gray-200">

                <div className="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mb-8 cursor-pointer" onClick={onClose} />

                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-extrabold tracking-tight text-gray-900">AI Weather Insight</h2>
                    <button onClick={onClose} className="w-10 h-10 flex items-center justify-center bg-gray-100 rounded-full hover:bg-gray-200 font-bold text-gray-600 transition-colors">
                        ✕
                    </button>
                </div>

                {isLoading && (
                    <div className="flex flex-col items-center justify-center p-16 opacity-70 animate-pulse">
                        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
                        <p className="font-bold text-gray-600 text-base">Analyzing personalization context...</p>
                    </div>
                )}

                {isError && (
                    <div className="p-6 bg-red-50 text-red-800 border border-red-100 rounded-2xl font-bold">
                        Failed to generate explanation. The backing engine may be offline.
                    </div>
                )}

                {data && (
                    <div className="space-y-8">
                        <div className="p-6 bg-blue-50/50 border border-blue-100 rounded-2xl shadow-sm">
                            <p className="font-bold text-blue-900 leading-relaxed text-lg">
                                {data.text}
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="p-5 border rounded-2xl border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow">
                                <h3 className="font-black text-[11px] text-gray-400 uppercase tracking-widest mb-4">Context Signals Used</h3>
                                <ul className="space-y-4">
                                    {data.signal_refs.map((sig: any, idx: number) => (
                                        <li key={idx} className="flex justify-between items-center text-sm">
                                            <span className="font-bold text-gray-700 capitalize w-2/3 truncate pr-2">{sig.signal.replace(/_/g, ' ')}</span>
                                            <span className="font-mono text-gray-600 bg-gray-50 border border-gray-100 px-2 py-1 rounded shadow-sm text-xs">
                                                {sig.value !== null ? sig.value.toString() : "N/A"}
                                            </span>
                                        </li>
                                    ))}
                                    {data.signal_refs.length === 0 && <span className="text-gray-400 text-sm font-bold">No particular signals referenced.</span>}
                                </ul>
                            </div>

                            <div className="p-5 border rounded-2xl border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow">
                                <h3 className="font-black text-[11px] text-gray-400 uppercase tracking-widest mb-4">Ranking Math</h3>
                                <div className="space-y-4">
                                    {Object.entries(data.score_components).map(([key, val], idx) => (
                                        <div key={idx} className="flex justify-between items-center text-sm">
                                            <span className="text-gray-700 font-bold capitalize">{key.replace(/_/g, ' ')}</span>
                                            <span className="font-mono text-blue-700 font-bold bg-blue-50 border border-blue-100 px-2 py-1 rounded shadow-sm text-xs">
                                                {Number(val).toFixed(2)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <button
                            className="w-full mt-6 p-4 rounded-xl bg-gray-900 text-white font-bold text-lg tracking-wide hover:-translate-y-0.5 shadow-lg active:bg-black transition-all"
                            onClick={onClose}
                        >
                            Got it
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}
