# Yahboom Raspbot v2 and voice (TTS/STT) — usability with Speech-MCP

Fleet / humanoid voice architecture: [HUMANOID_VOICE.md](HUMANOID_VOICE.md) · Voice Command Bus: [VOICE_COMMAND_BUS.md](VOICE_COMMAND_BUS.md)

**Usable?** Yes — on the robot for local TTS/STT; with Speech-MCP only via a bridge (robot STT → Speech-MCP, Speech-MCP → robot TTS/playback). See below.

## Raspbot v2 and the voice module

The **Yahboom Raspbot v2** is an AI vision robot car for Raspberry Pi 5 (Mecanum wheels, ROS2 Humble). Yahboom sells a separate **Intelligent Voice Interaction Module** (ASR-TTS) that can be used with it.

### Voice module (ASR-TTS)

- **Chip**: CI1302.
- **Features**: TTS (text-to-speech) and STT (speech-to-text); 110+ preset commands; custom Chinese/English wake and command words; ~99% recognition within 5 m with noise reduction and echo cancellation.
- **Interface**: IIC / serial / Type-C.
- **Software**: ROS1 and ROS2 SDK; on-board STC8H coprocessor converts voice to serial/IIC for the Pi.
- **Typical use on the car**: Wake word (e.g. “Hi Yahboom”), then voice commands for movement, lights, etc.

References: [Yahboom Voice Module ASR-TTS](https://www.yahboom.net/study/Voice_Module_ASR-TTS), [Raspbot V2](https://www.yahboom.net/study/RASPBOT-V2).

## Is it usable with Speech-MCP?

**Short answer:** The module is **usable on the robot** for local wake word + commands and onboard TTS. **Direct** use with Speech-MCP is not built-in; it becomes usable with Speech-MCP only via a **bridge** that connects the two.

- **Robot-side (as-is)**  
  The module gives you **on-device** STT (transcribed text / command IDs) and TTS (play audio from text). That is independent of Speech-MCP and works with the Raspbot’s ROS2/Serial stack.

- **Speech-MCP (cloud/PC)**  
  Speech-MCP provides Hume EVI, Hume/ElevenLabs/Windows TTS, RAG, and MCP tools. It runs as a service (e.g. on a PC or server), not on the robot.

- **Making them work together**  
  To use the robot’s TTS/STT *with* Speech-MCP you need a small integration layer that:

  1. **STT → Speech-MCP**  
     - Robot STT (or ROS2 node that wraps the module) produces text or command.  
     - A bridge (e.g. on the Pi or on a PC) sends that text to Speech-MCP (e.g. as EVI input or as a query for TTS/RAG).  
  2. **Speech-MCP → TTS on robot**  
     - Speech-MCP returns text (and optionally audio from Hume/ElevenLabs).  
     - The bridge either:  
       - Sends **text** to the robot (e.g. via ROS2 topic or HTTP), and the **Yahboom TTS module** does the synthesis on the robot, or  
       - Sends **audio** to the robot for playback (if the robot stack supports raw audio and the module or another player can play it).

So: **yes, the Yahboom TTS/STT module is usable**; with a bridge, the same pipeline can also drive or be driven by Speech-MCP (EVI, cloud TTS, RAG). The bridge can live in **yahboom-mcp** (e.g. a node that subscribes to robot STT and calls Speech-MCP, and publishes TTS text or audio to the robot) or in a small standalone service.

## Summary

| Question | Answer |
|----------|--------|
| Does Raspbot v2 have a TTS/STT module? | Yes, as an optional **Yahboom Voice Interaction Module** (CI1302, IIC/serial/Type-C, ROS1/2 SDK). |
| Is it usable on the robot? | Yes, for local wake word, commands, and onboard TTS. |
| Usable with Speech-MCP directly? | No; Speech-MCP does not talk to the module or ROS2 directly. |
| Usable with Speech-MCP via a bridge? | Yes; a bridge (e.g. in yahboom-mcp or a small service) can connect robot STT → Speech-MCP and Speech-MCP TTS/text → robot TTS/playback. |
