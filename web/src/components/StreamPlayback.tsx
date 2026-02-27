import React, { useEffect, useRef, useState } from 'react';

interface StreamPlaybackProps {
    streamUrl: string | null;
    provider: 'hume' | 'elevenlabs' | 'windows';
    text?: string;
}

export const StreamPlayback: React.FC<StreamPlaybackProps> = ({ streamUrl, provider, text }) => {
    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const [status, setStatus] = useState<'idle' | 'connecting' | 'streaming' | 'error'>('idle');

    useEffect(() => {
        if (!streamUrl) return;

        let isMounted = true;

        const initPlayback = async () => {
            // Avoid synchronous status change in effect
            await new Promise(resolve => setTimeout(resolve, 0));
            if (!isMounted) return;

            setStatus('connecting');

            const socket = new WebSocket(streamUrl);
            socketRef.current = socket;

            // Initialize AudioContext
            const AudioContextClass = (window as any).AudioContext || (window as any).webkitAudioContext;
            const audioCtx = new AudioContextClass();
            audioContextRef.current = audioCtx;

            socket.onopen = () => {
                if (isMounted) setStatus('streaming');
                if ((provider === 'elevenlabs' || provider === 'windows') && text) {
                    socket.send(JSON.stringify({ type: 'tts', text }));
                }
            };

            socket.onmessage = async (event: MessageEvent) => {
                if (event.data instanceof Blob) {
                    try {
                        const arrayBuffer = await event.data.arrayBuffer();
                        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
                        const source = audioCtx.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(audioCtx.destination);
                        source.start();
                    } catch (e) {
                        console.error("Audio decoding error:", e);
                    }
                }
            };

            socket.onerror = () => {
                if (isMounted) setStatus('error');
            };

            socket.onclose = () => {
                if (isMounted) setStatus('idle');
            };
        };

        initPlayback();

        return () => {
            isMounted = false;
            socketRef.current?.close();
            audioContextRef.current?.close();
        };
    }, [streamUrl, provider, text]);

    return (
        <div className="glass-card p-4 mt-4 animate-fade-in border border-white/5 bg-slate-900/40 backdrop-blur-md rounded-2xl">
            <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${status === 'streaming' ? 'bg-green-500 animate-pulse' :
                    status === 'connecting' ? 'bg-yellow-500' : 'bg-gray-500'
                    }`} />
                <span className="text-sm font-black text-white/70 uppercase tracking-widest">
                    {provider} Node: {status}
                </span>
            </div>
            {status === 'streaming' && (
                <div className="mt-2 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-indigo-500 animate-progress-indefinite w-1/3" />
                </div>
            )}
        </div>
    );
};
