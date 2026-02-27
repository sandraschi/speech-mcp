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

        setStatus('connecting');
        const socket = new WebSocket(streamUrl);
        socketRef.current = socket;

        // Initialize AudioContext for binary playback
        const AudioContextClass = (window as any).AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioContextClass();
        audioContextRef.current = audioCtx;

        socket.onopen = () => {
            setStatus('streaming');
            if ((provider === 'elevenlabs' || provider === 'windows') && text) {
                socket.send(JSON.stringify({ type: 'tts', text }));
            }
        };

        socket.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                const arrayBuffer = await event.data.arrayBuffer();
                try {
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

        socket.onerror = () => setStatus('error');
        socket.onclose = () => setStatus('idle');

        return () => {
            socket.close();
            audioCtx.close();
        };
    }, [streamUrl, provider, text]);

    return (
        <div className="glass-card p-4 mt-4 animate-fade-in">
            <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${status === 'streaming' ? 'bg-green-500 animate-pulse' :
                    status === 'connecting' ? 'bg-yellow-500' : 'bg-gray-500'
                    }`} />
                <span className="text-sm font-medium opacity-80 uppercase tracking-wider">
                    {provider} Stream: {status}
                </span>
            </div>
            {status === 'streaming' && (
                <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-accent-primary animate-progress-indefinite" style={{ width: '40%' }} />
                </div>
            )}
        </div>
    );
};
