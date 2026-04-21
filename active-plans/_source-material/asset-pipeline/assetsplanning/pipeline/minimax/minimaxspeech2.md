> ## Documentation Index

> Fetch the complete documentation index at: https://platform.minimax.io/docs/llms.txt

> Use this file to discover all available pages before exploring further.



\# Synchronous Text-to-Speech Guide (WebSocket)



> Synchronous TTS allows real-time text-to-speech synthesis, handling up to 10,000 characters per request.



\## Supported Models



Below are the MiniMax speech models and their key features.



| Model            | Description                                                                                              |

| ---------------- | -------------------------------------------------------------------------------------------------------- |

| speech-2.8-hd    | Ultra-realistic quality featuring sound tags.                                                            |

| speech-2.8-turbo | Seamless speed meets natural flow                                                                        |

| speech-2.6-hd    | Ultra-low latency, intelligence parsing, and enhanced naturalness.                                       |

| speech-2.6-turbo | Faster, more affordable, and ideal for your agent.                                                       |

| speech-02-hd     | Superior rhythm and stability, with outstanding performance in replication similarity and sound quality. |

| speech-02-turbo  | Superior rhythm and stability, with enhanced multilingual capabilities and excellent performance.        |



\## Supported Languages



MiniMax TTS models provide strong cross-lingual capabilities, supporting 40 widely used global languages. Our goal is to break language barriers and build truly universal AI models.



| Support Languages |               |               |

| ----------------- | ------------- | ------------- |

| 1. Chinese        | 15. Turkish   | 28. Malay     |

| 2. Cantonese      | 16. Dutch     | 29. Persian   |

| 3. English        | 17. Ukrainian | 30. Slovak    |

| 4. Spanish        | 18. Thai      | 31. Swedish   |

| 5. French         | 19. Polish    | 32. Croatian  |

| 6. Russian        | 20. Romanian  | 33. Filipino  |

| 7. German         | 21. Greek     | 34. Hungarian |

| 8. Portuguese     | 22. Czech     | 35. Norwegian |

| 9. Arabic         | 23. Finnish   | 36. Slovenian |

| 10. Italian       | 24. Hindi     | 37. Catalan   |

| 11. Japanese      | 25. Bulgarian | 38. Nynorsk   |

| 12. Korean        | 26. Danish    | 39. Tamil     |

| 13. Indonesian    | 27. Hebrew    | 40. Afrikaans |

| 14. Vietnamese    |               |               |



\## Streaming Request Example



This guide demonstrates streaming playback of synthesized audio while saving the full audio file.



⚠️ Note: To play audio streams in real-time, install \[MPV player](https://mpv.io/installation/) first. Also, ensure your API key is set in the environment variable `MINIMAX\_API\_KEY`.



Request example:



<CodeGroup>

&#x20; ```python theme={null}



&#x20; import asyncio

&#x20; import websockets

&#x20; import json

&#x20; import ssl

&#x20; import subprocess

&#x20; import os



&#x20; model = "speech-2.8-hd"

&#x20; file\_format = "mp3"



&#x20; class StreamAudioPlayer:

&#x20;     def \_\_init\_\_(self):

&#x20;         self.mpv\_process = None



&#x20;     def start\_mpv(self):

&#x20;         """Start MPV player process"""

&#x20;         try:

&#x20;             mpv\_command = \["mpv", "--no-cache", "--no-terminal", "--", "fd://0"]

&#x20;             self.mpv\_process = subprocess.Popen(

&#x20;                 mpv\_command,

&#x20;                 stdin=subprocess.PIPE,

&#x20;                 stdout=subprocess.DEVNULL,

&#x20;                 stderr=subprocess.DEVNULL,

&#x20;             )

&#x20;             print("MPV player started")

&#x20;             return True

&#x20;         except FileNotFoundError:

&#x20;             print("Error: mpv not found. Please install mpv")

&#x20;             return False

&#x20;         except Exception as e:

&#x20;             print(f"Failed to start mpv: {e}")

&#x20;             return False



&#x20;     def play\_audio\_chunk(self, hex\_audio):

&#x20;         """Play audio chunk"""

&#x20;         try:

&#x20;             if self.mpv\_process and self.mpv\_process.stdin:

&#x20;                 audio\_bytes = bytes.fromhex(hex\_audio)

&#x20;                 self.mpv\_process.stdin.write(audio\_bytes)

&#x20;                 self.mpv\_process.stdin.flush()

&#x20;                 return True

&#x20;         except Exception as e:

&#x20;             print(f"Play failed: {e}")

&#x20;             return False

&#x20;         return False



&#x20;     def stop(self):

&#x20;         """Stop player"""

&#x20;         if self.mpv\_process:

&#x20;             if self.mpv\_process.stdin and not self.mpv\_process.stdin.closed:

&#x20;                 self.mpv\_process.stdin.close()

&#x20;             try:

&#x20;                 self.mpv\_process.wait(timeout=20)

&#x20;             except subprocess.TimeoutExpired:

&#x20;                 self.mpv\_process.terminate()



&#x20; async def establish\_connection(api\_key):

&#x20;     """Establish WebSocket connection"""

&#x20;     url = "wss://api.minimax.io/ws/v1/t2a\_v2"

&#x20;     headers = {"Authorization": f"Bearer {api\_key}"}



&#x20;     ssl\_context = ssl.create\_default\_context()

&#x20;     ssl\_context.check\_hostname = False

&#x20;     ssl\_context.verify\_mode = ssl.CERT\_NONE



&#x20;     try:

&#x20;         ws = await websockets.connect(url, additional\_headers=headers, ssl=ssl\_context)

&#x20;         connected = json.loads(await ws.recv())

&#x20;         if connected.get("event") == "connected\_success":

&#x20;             print("Connection successful")

&#x20;             return ws

&#x20;         return None

&#x20;     except Exception as e:

&#x20;         print(f"Connection failed: {e}")

&#x20;         return None



&#x20; async def start\_task(websocket):

&#x20;     """Send task start request"""

&#x20;     start\_msg = {

&#x20;         "event": "task\_start",

&#x20;         "model": model,

&#x20;         "voice\_setting": {

&#x20;             "voice\_id": "English\_expressive\_narrator",

&#x20;             "speed": 1,

&#x20;             "vol": 1,

&#x20;             "pitch": 0,

&#x20;             "english\_normalization": False

&#x20;         },

&#x20;         "audio\_setting": {

&#x20;             "sample\_rate": 32000,

&#x20;             "bitrate": 128000,

&#x20;             "format": file\_format,

&#x20;             "channel": 1

&#x20;         }

&#x20;     }

&#x20;     await websocket.send(json.dumps(start\_msg))

&#x20;     response = json.loads(await websocket.recv())

&#x20;     return response.get("event") == "task\_started"



&#x20; async def continue\_task\_with\_stream\_play(websocket, text, player):

&#x20;     """Send continue request and stream play audio"""

&#x20;     await websocket.send(json.dumps({

&#x20;         "event": "task\_continue",

&#x20;         "text": text

&#x20;     }))



&#x20;     chunk\_counter = 1

&#x20;     total\_audio\_size = 0

&#x20;     audio\_data = b""



&#x20;     while True:

&#x20;         try:

&#x20;             response = json.loads(await websocket.recv())



&#x20;             if "data" in response and "audio" in response\["data"]:

&#x20;                 audio = response\["data"]\["audio"]

&#x20;                 if audio:

&#x20;                     print(f"Playing chunk #{chunk\_counter}")

&#x20;                     audio\_bytes = bytes.fromhex(audio)

&#x20;                     if player.play\_audio\_chunk(audio):

&#x20;                         total\_audio\_size += len(audio\_bytes)

&#x20;                         audio\_data += audio\_bytes

&#x20;                         chunk\_counter += 1



&#x20;             if response.get("is\_final"):

&#x20;                 print(f"Audio synthesis completed: {chunk\_counter-1} chunks")

&#x20;                 if player.mpv\_process and player.mpv\_process.stdin:

&#x20;                     player.mpv\_process.stdin.close()



&#x20;                 # Save audio to file

&#x20;                 with open(f"output.{file\_format}", "wb") as f:

&#x20;                     f.write(audio\_data)

&#x20;                 print(f"Audio saved as output.{file\_format}")



&#x20;                 estimated\_duration = total\_audio\_size \* 0.0625 / 1000

&#x20;                 wait\_time = max(estimated\_duration + 5, 10)

&#x20;                 return wait\_time



&#x20;         except Exception as e:

&#x20;             print(f"Error: {e}")

&#x20;             break



&#x20;     return 10



&#x20; async def close\_connection(websocket):

&#x20;     """Close connection"""

&#x20;     if websocket:

&#x20;         try:

&#x20;             await websocket.send(json.dumps({"event": "task\_finish"}))

&#x20;             await websocket.close()

&#x20;         except Exception:

&#x20;             pass



&#x20; async def main():

&#x20;     API\_KEY = os.getenv("MINIMAX\_API\_KEY")

&#x20;     TEXT = "The real danger is not that computers start thinking like people(sighs), but that people start thinking like computers. Computers can only help us with simple tasks."



&#x20;     player = StreamAudioPlayer()



&#x20;     try:

&#x20;         if not player.start\_mpv():

&#x20;             return



&#x20;         ws = await establish\_connection(API\_KEY)

&#x20;         if not ws:

&#x20;             return



&#x20;         if not await start\_task(ws):

&#x20;             print("Task startup failed")

&#x20;             return



&#x20;         wait\_time = await continue\_task\_with\_stream\_play(ws, TEXT, player)

&#x20;         await asyncio.sleep(wait\_time)



&#x20;     except Exception as e:

&#x20;         print(f"Error: {e}")

&#x20;     finally:

&#x20;         player.stop()

&#x20;         if 'ws' in locals():

&#x20;             await close\_connection(ws)



&#x20; if \_\_name\_\_ == "\_\_main\_\_":

&#x20;     asyncio.run(main())

&#x20; ```

</CodeGroup>



\## Recommended Reading



<Columns cols={2}>

&#x20; <Card title="Text to Speech (T2A) WebSocket" icon="book-open" href="/api-reference/speech-t2a-websocket" arrow="true" cta="Click here">

&#x20;   Use this API for synchronous t2a over WebSocket.

&#x20; </Card>



&#x20; <Card title="Text to Speech (T2A) HTTP" icon="book-open" href="/api-reference/speech-t2a-http" arrow="true" cta="Click here">

&#x20;   Use this API for synchronous t2a over HTTP.

&#x20; </Card>



&#x20; <Card title="Pricing" icon="book-open" href="/guides/pricing-paygo#audio" arrow="true" cta="Click here">

&#x20;   Detailed information on model pricing and API packages.

&#x20; </Card>



&#x20; <Card title="Rate Limits" icon="book-open" href="/guides/rate-limits#3-rate-limits-for-our-api#3-rate-limits-for-our-api" arrow="true" cta="Click here">

&#x20;   Rate limits are restrictions that our API imposes on the number of times a user or client can access our services within a specified period of time.

&#x20; </Card>

</Columns>



