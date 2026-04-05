import React, { useEffect, useRef, useState } from 'react';

interface StreamPlaybackProps {
    streamUrl: string | null;
    provider: 'hume' | 'elevenlabs' | 'windows';
    text?: string;
    playKey?: number; // increment to force re-play same URL
}

export const StreamPlayback: React.FC<StreamPlaybackProps> = ({ streamUrl, provider, text, playKey }) => {
    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const chunksRef = useRef<Uint8Array[]>([]);
    const [status, setStatus] = useState<'idle' | 'connecting' | 'streaming' | 'playing' | 'error'>('idle');
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        if (!streamUrl) return;

        // Close any previous connection
        socketRef.current?.close();
        audioContextRef.current?.close().catch(() => {});
        chunksRef.current = [];

        let isMounted = true;
        setStatus('connecting');
        setErrorMsg('');

        const AudioContextClass = (window as any).AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioContextClass();
        audioContextRef.current = audioCtx;

        const socket = new WebSocket(streamUrl);
        socketRef.current = socket;
        socket.binaryType = 'arraybuffer';

        socket.onopen = () => {
            if (!isMounted) return;
            setStatus('streaming');
            // Send TTS request immediately on connect
            if ((provider === 'elevenlabs' || provider === 'windows') && text) {
                socket.send(JSON.stringify({ type: 'tts', text }));
            }
        };

        socket.onmessage = async (event: MessageEvent) => {
            if (!isMounted) return;
            if (event.data instanceof ArrayBuffer && event.data.byteLength > 0) {
                chunksRef.current.push(new Uint8Array(event.data));
            }
        };

        socket.onclose = async () => {
            if (!isMounted) return;
            // All chunks received — decode and play
            const chunks = chunksRef.current;
            if (chunks.length > 0) {
                setStatus('playing');
                try {
                    // Concatenate all chunks into a single buffer
                    const totalLen = chunks.reduce((acc, c) => acc + c.byteLength, 0);
                    const merged = new Uint8Array(totalLen);
                    let offset = 0;
                    for (const c of chunks) {
                        merged.set(c, offset);
                        offset += c.byteLength;
                    }
                    const audioBuffer = await audioCtx.decodeAudioData(merged.buffer);
                    const source = audioCtx.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(audioCtx.destination);
                    source.onended = () => { if (isMounted) setStatus('idle'); };
                    source.start();
                } catch (e) {
                    console.error('Audio decode error:', e);
                    if (isMounted) {
                        setErrorMsg(`Decode failed: ${e instanceof Error ? e.message : String(e)}`);
                        setStatus('error');
                    }
                }
            } else {
                if (isMounted) setStatus('idle');
            }
        };

        socket.onerror = (e) => {
            console.error('WebSocket error:', e);
            if (isMounted) {
                setErrorMsg('WebSocket connection failed');
                setStatus('error');
            }
        };

        return () => {
            isMounted = false;
            socketRef.current?.close();
            audioContextRef.current?.close().catch(() => {});
        };
    // playKey in deps so same URL can re-trigger
    }, [streamUrl, provider, text, playKey]); // eslint-disable-line react-hooks/exhaustive-deps

    if (status === 'idle') return null;

    return (
        <div className="glass-card p-4 mt-2 animate-fade-in border border-white/5 bg-slate-900/40 backdrop-blur-md rounded-2xl">
            <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
                    status === 'playing'    ? 'bg-emerald-500 animate-pulse' :
                    status === 'streaming' ? 'bg-yellow-400 animate-pulse' :
                    status === 'connecting' ? 'bg-yellow-600' :
                    status === 'error'     ? 'bg-rose-500' :
                    'bg-gray-500'
                }`} />
                <span className="text-sm font-black text-white/70 uppercase tracking-widest">
                    {provider}: {status}
                </span>
                {errorMsg && <span className="text-xs text-rose-400 ml-2">{errorMsg}</span>}
            </div>
            {(status === 'streaming' || status === 'playing') && (
                <div className="mt-2 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-indigo-500 animate-[progress_2s_ease-in-out_infinite] w-1/3" />
                </div>
            )}
        </div>
    );
};
