import pyaudio
import wave
import numpy
import psutil, os
import time
import scipy.signal as signal
from multiprocessing import Process, Value, Lock
import pygame
import alsaaudio

ratio = 1.0
final = numpy.ones((1024,2))



def play(device, f):    

    print('%d channels, %d sampling rate\n' % (f.getnchannels(),
                                               f.getframerate()))
    print(f.getsampwidth())
    # Set attributes
    device.setchannels(f.getnchannels())
    #device.setrate(f.getframerate())
    device.setrate(44800)
    # 8bit is unsigned in wav files
    if f.getsampwidth() == 1:
        device.setformat(alsaaudio.PCM_FORMAT_U8)
    # Otherwise we assume signed data, little endian
    elif f.getsampwidth() == 2:
        device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    elif f.getsampwidth() == 3:
        device.setformat(alsaaudio.PCM_FORMAT_S24_LE)
    elif f.getsampwidth() == 4:
        device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
    else:
        raise ValueError('Unsupported format')

    device.setperiodsize(320)
    
    data = f.readframes(320)
    while data:
        # Read data from stdin
        device.write(data)
        data = f.readframes(320)






def get_callback(waf):
    wf = waf
    def callback(in_data, frame_count, time_info, status):
        #print(in_data, frame_count, time_info, status)
        #print(wf)
        global ratio
        #wf = wave_form
        data = wf.readframes(frame_count)
        #return (data, pyaudio.paContinue)

        return
        round_data = (int)(frame_count*ratio)

        if round_data % 2 != 0:
            round_data += 1
        data = wf.readframes(round_data)




        #if data == '':
        #    wf.rewind()
        #    data = wf.readframes(round_data)
        result = numpy.fromstring(data, dtype=numpy.int16)
        #print(status)
        #print(result.size)
        if result.size != 0:
            if wf.getnchannels() == 2:
                result = numpy.reshape(result, (result.size/2, 2))
                #split data into seperate channels and resample
                final[:, 0] = signal.resample(result[:, 0], 1024)
                final[:, 1] = signal.resample(result[:, 1], 1024)
                out_data = final.flatten().astype(numpy.int16).tostring()
            elif wf.getnchannels() == 1:
                print('doin one channel')
                out_data = signal.resample(result, 1024).astype(numpy.int16).tostring()
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

    device = alsaaudio.PCM(card=None)
    f = wave.open('audio/Joust/music/classical.wav', 'rb')
    play(device, f)
    return

    #pygame.mixer.init()
    #effect = pygame.mixer.Sound('audio/Joust/sounds/cyan team win.wav')
    #effect.play()
    while True:
        
        #wf = 1



        
        wf = wave.open(str(file), 'rb')
        data = wf.readframes(1024)
        result = numpy.fromstring(data, dtype=numpy.int16)
        result = numpy.reshape(result, (result.size/2, 2))
        #print(result.shape)
        snd_out = pygame.sndarray.make_sound(result)
        snd_out.play()
        continue




        p = pyaudio.PyAudio()
    
        #wf = wave.open('audio/Joust/sounds/cyan team win.wav', 'rb')
        print (wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), p.get_format_from_width(wf.getsampwidth()))
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



def audio_effect(file, p, proc_ratio, end, chunk_size, stop_proc):
    wf = wave.open('audio/Joust/sounds/cyan team win.wav', 'rb')
    CHUNK = 1024
    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    # open stream (2)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    frames_per_buffer = CHUNK)

    # read data
    data = wf.readframes(CHUNK)

    # play stream (3)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

    # stop stream (4)
    stream.stop_stream()
    stream.close()

    # close PyAudio (5)
    p.terminate()

    



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

        #pygame.mixer.init()
        #pygame.mixer.init(47000, -16, 2, 4096)
        #self.effect = pygame.mixer.Sound(self.file)
        #self.effect.play()
        #device = alsaaudio.PCM(card=None)
        #f = wave.open('audio/Joust/music/classical.wav', 'rb')
        #self.play(device, f)


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
        #self.proc = Process(target=audio_effect, args=(self.file, self.p, self.ratio, self.end, self.chunk_size, self.stop_proc))
        #self.proc.start()
        #pygame.mixer.init(47000, -16, 2, 4096)
        #self.effect = pygame.mixer.Sound(self.file)
        #self.effect.play()
        device = alsaaudio.PCM(card=None)
        f = wave.open(self.file, 'rb')
        play(device, f)

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
            
        
          
