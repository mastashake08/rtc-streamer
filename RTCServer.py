import argparse
import asyncio
import logging
import qrcode
import zlib
import base64

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaBlackhole, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling



async def run(pc,recorder, signaling, role):
 
       
    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)

    # connect signaling
    await signaling.connect()

    if role == "offer":
        # send offer

        pc.createDataChannel('Test')
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
       
        qr = qrcode.QRCode(
            box_size=1,  # Use small 1x1 'pixels' in ASCII
            border=1,    # Minimal border
            )
        try:
            qr.add_data(pc.localDescription.sdp)
        except:
            compressed_bytes = zlib.compress(pc.localDescription.sdp.encode("utf-8"))
            b64_compressed = base64.urlsafe_b64encode(compressed_bytes).decode("ascii")
            qr.add_data(b64_compressed)
        qr.make(fit=True)

        # Print ASCII QR code in the terminal.
        # 'invert=True' switches black/white in ASCII, which can help scanning.
        qr.print_ascii(invert=True)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--record-to", help="Write received media to a file.")
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = create_signaling(args)
    pc = RTCPeerConnection()
    # add recvonly transceiver
    pc.addTransceiver("audio", direction="recvonly")
    pc.addTransceiver("video", direction="recvonly")
   

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                recorder=recorder,
                signaling=signaling,
                role=args.role,
            )
        )
    except KeyboardInterrupt:
        logging.info("Shutting Down...")
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
