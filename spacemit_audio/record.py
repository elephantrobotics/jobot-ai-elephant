import webrtcvad
import pyaudio
import tempfile
import wave
import time
import threading

class RecAudio:
    def __init__(self, vad_mode=1, sld=1, max_time=5, channels=1, rate=48000, device_index=0):
        """
        Args:
            vad_mode: vad 的模式
            sld: 静音多少 s 停止录音
            max_time: 最多录音多少秒
            channels: 声道数
            rate: 采样率
            device_index: 输入的设备索引
        """
        self._mode = vad_mode
        self._sld = sld
        self.max_time_record = max_time
        self.frame_is_append = False
        self.time_start = time.time()

        # 参数配置
        self.FORMAT = pyaudio.paInt16  # 16-bit 位深
        self.CHANNELS = channels              # 单声道
        self.RATE = rate              # 16kHz 采样率
        FRAME_DURATION = 30       # 每帧时长（ms）
        self.FRAME_SIZE = int(self.RATE * FRAME_DURATION / 3000)  # 每帧采样数

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
        """带有VAD的录音实现"""
        # 变量初始化
        frames = []                # 存储录制的音频帧
        speech_detected = False    # 是否已检测到人声
        last_speech_time = time.time()  # 最后检测到人声的时间
        MIN_SPEECH_DURATION = 1.0       # 最短录制时间（秒），避免误触发

        self.time_start = time.time()   # 用于最长录制时间的计时

        temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_wav_path = temp_wav_file.name
        print(temp_wav_path)

        try:
            while True:    
                frame = self.stream.read(self.FRAME_SIZE, exception_on_overflow=False) # 读取一帧音频数据
                
                is_speech = self.vad.is_speech(frame, self.RATE) # VAD 检测是否含人声
                if is_speech:
                    # 检测到人声，更新最后活动时间
                    last_speech_time = time.time()
                    if not speech_detected:
                        speech_detected = True
                        print("检测到语音，开始录制...")
                
                # 如果已经开始录制，保存音频帧
                if self.frame_is_append:
                    frames.append(frame)
                
                # 静音超时判断（且满足最短录制时间）
                current_time = time.time()
                if (speech_detected and 
                    current_time - last_speech_time > self._sld and
                    current_time - last_speech_time > MIN_SPEECH_DURATION):
                    print(f"静音超过 {self._sld} 秒，停止录制。")
                    break

                # 录音时间超过设定的最长时间
                if speech_detected and (time.time() - self.time_start) >= self.max_time_record:
                    print(f"录音时间超过 {self.max_time_record} 秒，停止录制。")
                    break

        except KeyboardInterrupt:
            print("手动中断录制。")

        finally:
            # 停止并关闭音频流
            print("关闭音频流")
            self.stream.stop_stream()

            if len(frames) > 0:
                with wave.open(temp_wav_path, "wb") as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.pa.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b"".join(frames))
                # print("音频已保存为 temp_wav_file")
                return temp_wav_path

    def record_audio(self):
        """触发录音的函数"""
        self.stream.start_stream()
        temp_wav_file_path = self.vad_audio()
        return temp_wav_file_path


class RecAudioThread(RecAudio):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread = None
        self.is_recording = False
        self.audio_file_path = None  # 录音文件路径

    def start_recording(self):
        """启动录音线程"""
        if self.thread is None or not self.thread.is_alive():
            self.is_recording = True
            self.thread = threading.Thread(target=self._record_audio_thread)
            self.thread.start()

    def _record_audio_thread(self):
        """录音线程执行的方法"""
        self.audio_file_path = self.record_audio()
        self.is_recording = False

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def get_audio_file(self):
        """获取录音后的文件路径"""
        return self.audio_file_path
