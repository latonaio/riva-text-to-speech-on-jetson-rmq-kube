import asyncio
import os
import queue
import threading
from functools import partial
from traceback import print_exc

import grpc
import numpy as np
import sounddevice as sd
import riva_api.riva_tts_pb2 as rtts
import riva_api.riva_tts_pb2_grpc as rtts_srv
import riva_api.riva_audio_pb2 as ra
from rabbitmq_client import RabbitmqClient

SAMPLE_RATE = 44100             # Sampling Rate
REQUESTED_DATA_SIZE = 384       # Size of data that can be pronouned at once.
AUDIO_BUFFER_SIZE = 8192        # Max size of audio buffer queue

def callback(queue, outdata, frames, time, status):
  _, n_channels = outdata.shape

  # Get data from queue and play audio.
  if not queue.empty():
    data = queue.get_nowait()
    for k in range(n_channels):
      outdata[:, k] = data

async def text_to_speech(queue, text):
  req = rtts.SynthesizeSpeechRequest(
    text = text,
    language_code = "en-US",
    encoding = ra.AudioEncoding.LINEAR_PCM,    # Currently only LINEAR_PCM is supported.
    sample_rate_hz = SAMPLE_RATE,              # Generate 44.1KHz audio
    voice_name = "English-US-Female-1"         # The name of the voice to generate
  )
  responses = await asyncio.to_thread(riva_tts.SynthesizeOnline, req)

  for resp in responses:
    # Process data into the form of audio data.
    datalen = len(resp.audio) // 2
    data16 = np.ndarray(buffer=resp.audio, dtype=np.int16, shape=(datalen, 1))
    speech = bytes(data16.data)
    data = np.frombuffer(speech, dtype=np.int16)

    # Put audio data (numpy array) into queue.
    for i in range(len(data)//REQUESTED_DATA_SIZE):
      if i == len(data)//REQUESTED_DATA_SIZE:
        break

      await asyncio.to_thread(queue.put, data[REQUESTED_DATA_SIZE*i:REQUESTED_DATA_SIZE*(i+1)])

def play_buffer_audio(queue):
  event = threading.Event()

  stream = sd.OutputStream(
    channels=2, dtype='int16', callback=partial(callback, queue), finished_callback=event.set
  )

  with stream:
    event.wait()

async def main():
  url = os.environ['RABBITMQ_URL']
  queue_origin = os.environ['QUEUE_ORIGIN']
  client = await RabbitmqClient.create(url, {queue_origin}, {})

  buffer_queue = queue.Queue(maxsize=AUDIO_BUFFER_SIZE)
  thread = threading.Thread(target=play_buffer_audio, args=[buffer_queue])
  thread.start()

  # Recieve message from RabbitMQ.
  async for message in client.iterator():
    try:
      async with message.process():
        text = message.data['transcript']
        await text_to_speech(buffer_queue, text)
    except Exception:
      print_exc()

if __name__ == '__main__':
  sd.default.device = int(os.environ['DEVICE_ID'])
  channel = grpc.insecure_channel(os.environ['SERVER_ADDRESS'])
  riva_tts = rtts_srv.RivaSpeechSynthesisStub(channel)

  asyncio.run(main())
