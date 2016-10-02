import pyaudio
import wave
import numpy
import psutil, os
import time
import scipy.signal as signal
from multiprocessing import Process, Value, Lock
import pygame

ratio = 1.0
final = numpy.ones((1024,2))
def get_callback(waf):
    wf = waf
    def callback(in_data, frame_count, time_info, status):
        #print(in_data, frame_count, time_info, status)
        #print(wf)
        global ratio
        #wf = wave_form


        #data = wf.readframes(frame_count)
        #return (data, pyaudio.paContinue)

        round_data = (int)(frame_count*ratio)

        if round_data % 2 != 0:
            round_data += 1
        data = wf.readframes(round_data)




        #if data == '':
        #    wf.rewind()
        #    data = wf.readframes(round_data)
        result = numpy.fromstring(data, dtype=numpy.int16)
        #print(status)
        print(result.size)
        if result.size != 0:

            result = numpy.reshape(result, (result.size/2, 2))
            #split data into seperate channels and resample
            final[:, 0] = signal.resample(result[:, 0], 1024)
            final[:, 1] = signal.resample(result[:, 1], 1024)
            out_data = final.flatten().astype(numpy.int16).tostring()
            return (out_data, pyaudio.paContinue)
        else:
            print('no blue')
            return (data, pyaudio.paContinue)
    return callback


def audio_loop(file, p, proc_ratio, end, chunk_size, stop_proc):
    global ratio
    #global wf

    time.sleep(0.5)
    #proc = psutil.Process(os.getpid())
    #proc.nice(-5)
    time.sleep(0.02)
    print ('bipandpap')
    print ('file is ' + str(file))

    
    while True:
        p = pyaudio.PyAudio()
        #wf = 1
        wf = wave.open(str(file), 'rb')
        #wf = wave.open('audio/Joust/sounds/cyan team win.wav', 'rb')
        print (wf.getnchannels(), wf.getsampwidth(), wf.getframerate())
        #wf.rewind()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=get_callback(wf))




        #stream.start_stream()
        #print ('starting stream')
        while stream.is_active() and stop_proc.value == 0:
            ratio = proc_ratio.value
            time.sleep(0.1)
        #wf.rewind()
        print('broke out')
        #print(stream.is_active())
        #print(stop_proc.value)
        stream.stop_stream()
        stream.close()
        wf.rewind()
        wf.close()
        #wf = wave.open('audio/Joust/sounds/join.wav', 'rb')
        #print('doing 222')
        #stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
        #                channels=wf.getnchannels(),
        #                rate=wf.getframerate(),
        #                output=True,
        #                stream_callback=get_callback(wf))

        #while stream.is_active() and stop_proc.value == 0:
        #    ratio = proc_ratio.value
        #    time.sleep(0.1)
        stream.close()
        p.terminate()
        wf.close()

        if end or stop_proc.value == 1:
            break
    stream.stop_stream()
    stream.close()
    
    #
    return



    
    #while True:
        #chunk = 2048/2
    #    wf = wave.open(file, 'rb')
    #    time.sleep(0.03)
    #    data = wf.readframes(chunk_size.value)
    #    time.sleep(0.03)
        #import pdb; pdb.set_trace()
    #    stream = p.open(
    #        format = p.get_format_from_width(wf.getsampwidth()), 
    #        channels = wf.getnchannels(),
    #        rate = wf.getframerate(),
    #        output = True,
    #        frames_per_buffer = chunk_size.value)

        #while not end or stop_proc.value != 1:
        #    time.sleep(0.1)
    #    while data != '' and stop_proc.value == 0:

    #        array = numpy.fromstring(data, dtype=numpy.int16)
    #        data = signal.resample(array, chunk_size.value*ratio.value)
    #        stream.write(data.astype(int).tostring())
    #        data = wf.readframes(chunk_size.value)

    #    stream.stop_stream()
    #    stream.close()
    #    wf.close()
    #    p.terminate()
        
    #    if end or stop_proc.value == 1:
    #        break
    #stream.stop_stream()
    #stream.close()
    #wf.close()
    #p.terminate()




# Start audio in seperate process to be non-blocking
class Audio:
    def __init__(self, file, end=False):
        print('doin init@@@@@@@@@@@@@@')
        
        self.stop_proc = Value('i', 0)
        self.chunk = 2048
        self.file = file
        self.ratio = Value('d' , 1.0)
        self.chunk_size = Value('i', int(2048/2))
        self.end = end
        





        
        #pygame.mixer.init(44100, -16, 2 , 2048)
        #hey
        #pygame.mixer.init()
        #pygame.mixer.init(47000, -16, 2 , 4096)

        wf = wave.open('audio/Joust/music/classical.wav', 'rb')

        self.p = pyaudio.PyAudio()

    def start_audio_loop(self):
        print('starting audio loop')

        #audio_loop(self.file, self.p, self.ratio, self.end, self.chunk_size, self.stop_proc)
        self.proc = Process(target=audio_loop, args=(self.file, self.p, self.ratio, self.end, self.chunk_size, self.stop_proc))
        self.proc.start()
        
    def stop_audio(self):
        self.stop_proc.value = 1
        #self.p.terminate()
        self.proc.join()

    def change_ratio(self, ratio):
        self.ratio.value = ratio

    def change_chunk_size(self, increase):
        if increase:
            self.chunk_size.value = int(2048/4)
        else:
            self.chunk_size.value = int(2048/2)

    def start_effect(self):
        #self.effect = pygame.mixer.Sound(self.file)
        #self.effect.play()
        pass

    def stop_effect(self):
        return
        self.effect.stop()

    def start_effect_music(self):
        return
        pygame.mixer.music.load(self.file)
        pygame.mixer.music.play()

    def stop_effect_music(self):
        return
        pygame.mixer.music.fadeout(1)
            
        
          
