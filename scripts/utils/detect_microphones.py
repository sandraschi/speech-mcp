import pyaudio


def get_microphones():
    p = pyaudio.PyAudio()
    mics = []

    # Get device count
    count = p.get_device_count()

    # Iterate through devices
    for i in range(count):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            mics.append({
                "index": i,
                "name": info.get('name'),
                "channels": info.get('maxInputChannels'),
                "rate": info.get('defaultSampleRate')
            })

    p.terminate()
    return mics

if __name__ == "__main__":
    mics = get_microphones()
    print(f"Detected {len(mics)} Microphones/Input Devices:")
    for m in mics:
        print(f"  [{m['index']}] {m['name']} ({m['channels']} channels, {m['rate']} Hz)")
