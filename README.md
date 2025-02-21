# Receive-Only WebRTC with ASCII QR Code SDP

This repository (or script) demonstrates a **receive-only** WebRTC connection using [aiortc](https://github.com/aiortc/aiortc). The script can run in **offer** or **answer** role. When running in the `offer` role, it prints the local SDP as a compressed **ASCII QR code** directly in the terminal. This allows you to easily transfer the SDP to another device or peer without copying and pasting long text.

## Features

- **Receive-only** audio and video transceivers.
- Generates a **compressed** SDP offer, encodes it with `base64`, and prints it as an **ASCII QR code** in the terminal if `role=offer`.
- Handles incoming media tracks with `MediaRecorder` (saves to file) or `MediaBlackhole` (discards).
- Uses [aiortc.contrib.signaling](https://aiortc.readthedocs.io/en/latest/signaling.html) to exchange signaling data (SDP and ICE candidates).

## Prerequisites

- Python 3.7+ (recommended)
- Install the following Python packages:
  ```bash
  pip install aiortc qrcode
  ```
  - `aiortc` handles the WebRTC connection.
  - `qrcode` prints ASCII QR codes in the terminal.
  - `pillow` may be required by `qrcode` for some features. If you run into issues, do:
    ```bash
    pip install pillow
    ```

## Usage

### 1. Command-Line Arguments

| Argument         | Description                                                              |
|------------------|--------------------------------------------------------------------------|
| `role`           | **Required**. Either `offer` or `answer`. Determines the WebRTC role.    |
| `--record-to`    | (Optional) File path to record received media. E.g., `record.mp4`        |
| `--verbose` / `-v` | (Optional) Increase logging verbosity. Can be repeated for more detail.|
| Signaling Args   | Provided by `add_signaling_arguments(parser)` from aiortc. You’ll specify which signaling method to use (e.g. `--signaling json`, `--signaling tcp`, etc.) |

### 2. Example: Running as Offer

```bash
python receive_only_qr.py offer --signaling json
```

1. The script adds two transceivers in **receive-only** mode.
2. It creates an SDP offer, compresses and Base64-encodes it.
3. The script prints an **ASCII QR code** in the terminal.  
4. Scan or share this QR code with the peer. (The peer should decode the compressed SDP, then set it as their remote description.)

> **Tip**: You may need to **resize** your terminal window or adjust **font size** so that the QR code is easier to scan.

### 3. Example: Running as Answer

```bash
python receive_only_qr.py answer --signaling json
```

1. The script waits to receive an offer (and ICE candidates) from the signaling channel.
2. Once it has the offer, it sets the remote description, and starts a `MediaRecorder` or `MediaBlackhole`.
3. It does not generate a QR code in this role.

## How It Works

1. **Create PeerConnection**  
   ```python
   pc = RTCPeerConnection()
   pc.addTransceiver("audio", direction="recvonly")
   pc.addTransceiver("video", direction="recvonly")
   ```
   This sets up two **receive-only** transceivers (one for audio, one for video).

2. **Offer Role**  
   - Calls `pc.createOffer()` and `pc.setLocalDescription(...)`.  
   - Compresses the SDP using `zlib.compress(...)` and encodes with Base64.  
   - Prints an ASCII QR code using the `qrcode` library.  
   - The remote peer scans (or otherwise obtains) the SDP, sets it as the remote offer, and responds with an answer.

3. **Answer Role**  
   - Waits for an incoming offer from the signaling channel.  
   - Once received, calls `pc.setRemoteDescription(...)`.  
   - Creates an answer automatically (not shown in the snippet, but typically done in a complete system).  

4. **Receiving Tracks**  
   - On the `pc.on("track")` event, we attach incoming tracks to a `MediaRecorder` or `MediaBlackhole`.  
   - This either **records** the track to a file (e.g., an MP4) or **discards** it.

5. **Signaling**  
   - The script uses `create_signaling(args)` from `aiortc.contrib.signaling` to handle exchanging SDP and ICE candidates.  
   - If you pass `--signaling json`, it uses a JSON file-based signaling. If you pass `--signaling tcp`, it uses a TCP-based approach, etc.

## Decoding the QR Code Offer

If you are scanning the QR code from a different machine or an external device:

1. **Scan the ASCII QR code** (you may need a dedicated QR scanning app that handles large data).  
2. The scanned text is a **Base64 (URL-safe) + zlib compressed** string.  
3. To decode:
   ```python
   import base64, zlib

   # Suppose `scanned_string` is what you got from the QR scanner
   compressed_bytes = base64.urlsafe_b64decode(scanned_string)
   original_sdp = zlib.decompress(compressed_bytes).decode("utf-8")

   print("Decoded SDP:", original_sdp)
   ```
4. Then set this `original_sdp` as your `pc.setRemoteDescription(RTCSessionDescription(original_sdp, "offer"))` in your answering script.

## Troubleshooting & Tips

- **QR Code Too Large**: If the script fails with a version error (e.g., “Invalid version (was 41, expected 1 to 40)”), your data may be too big. Possible solutions:
  - Use chunking (split the SDP into multiple smaller QR codes).  
  - Lower error correction.  
  - Provide a smaller STUN/TURN configuration or reduce offered codecs.
- **Scanning Difficulties**:
  - Try increasing your terminal size or adjusting font size.  
  - Ensure good contrast (light background, dark text).
- **Record to File**:
  - Use `--record-to=output.mp4` to record all incoming media to `output.mp4`.  
  - Make sure you have the necessary dependencies to encode that container format.

## License

This script is provided “as is,” under the same license as the [aiortc](https://github.com/aiortc/aiortc) examples, or your project’s chosen license.  

Enjoy using **receive-only WebRTC** with **ASCII QR code** for SDP exchange! If you run into issues, please report them or check out the [aiortc documentation](https://aiortc.readthedocs.io/).