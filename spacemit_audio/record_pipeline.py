import webrtcvad
import pyaudio
import tempfile
import wave
import time
import threading
import numpy as np
from scipy.signal import resample

class RecAudioPipeLine:
    def __init__(self, vad_mode=1, sld=1, max_time=5, channels=1, rate=48000, device_index=0):
        """
        Args:
            vad_mode: vad mode
            sld: how many seconds of silence to stop recording
            max_time: how many seconds of maximum recording
            channels: number of channels
            rate: sampling rate
            device_index: input device index
        """
        self._mode = vad_mode
        self._sld = sld
        self.max_time_record = max_time
        self.frame_is_append = False
        self.time_start = time.time()

        # Parameter configuration
        self.FORMAT = pyaudio.paInt16 # 16-bit bit depth
        self.CHANNELS = channels # Mono
        self.RATE = rate # 16kHz sampling rate
        FRAME_DURATION = 30 # Duration per frame (ms)
        self.FRAME_SIZE = int(self.RATE * FRAME_DURATION / 3000) # Number of samples per frame

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.FRAME_SIZE,
            input_device_index=device_index
        )

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self._mode)

    def vad_audio(self):
        """Recording with VAD"""
        frames = []
        speech_detected = False
        last_speech_time = time.time()
        MIN_SPEECH_DURATION = 1.0
        self.time_start = time.time()

        try:
            while True:
                frame = self.stream.read(self.FRAME_SIZE, exception_on_overflow=False)
                is_speech = self.vad.is_speech(frame, self.RATE)
                if is_speech:
                    last_speech_time = time.time()
                    if not speech_detected:
                        speech_detected = True
                        print("检测到语音，开始录制...")

                if self.frame_is_append:
                    frames.append(frame)

                current_time = time.time()
                if (speech_detected and
                    current_time - last_speech_time > self._sld and
                    current_time - last_speech_time > MIN_SPEECH_DURATION):
                    print(f"静音超过 {self._sld} 秒，停止录制。")
                    break

                if speech_detected and (current_time - self.time_start) >= self.max_time_record:
                    print(f"录音时间超过 {self.max_time_record} 秒，停止录制。")
                    break

        except KeyboardInterrupt:
            print("手动中断录制。")

        finally:
            print("关闭音频流")
            self.stream.stop_stream()

            if len(frames) > 0:
                # 转换为 numpy ndarray（int16 类型）
                audio_data = b"".join(frames)
                audio_np = np.frombuffer(audio_data, dtype=np.int16)

                if self.RATE != 16000:
                    num_samples = int(len(audio_np) * float(16000) / self.RATE)
                    waveform = resample(audio_np, num=num_samples)
                    return waveform
                else:
                    return audio_np
            else:
                return None

    def record_audio(self):
        self.stream.start_stream()
        audio_ndarray = self.vad_audio()
        return audio_ndarray


class RecAudioThreadPipeLine(RecAudioPipeLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread = None
        self.is_recording = False
        self.audio_ndarray = None  # Recording file path

    def start_recording(self):
        """Start recording thread"""
        if self.thread is None or not self.thread.is_alive():
            self.is_recording = True
            self.thread = threading.Thread(target=self._record_audio_thread)
            self.thread.start()

    def _record_audio_thread(self):
        """Methods executed by the recording thread"""
        self.audio_ndarray = self.record_audio()
        self.is_recording = False

    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def get_audio(self):
        """Get the file path after recording"""
        return self.audio_ndarray
