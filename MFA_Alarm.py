from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

from datetime import datetime
from threading import Thread
import random
import cv2
import time
import pygame

# Manajemen Alarm
class AlarmManager:
    alarm_active = False
    alarm_time = None
    is_playing = False
    sound = None

    @staticmethod
    def initialize():
        pygame.mixer.init()
        AlarmManager.sound = pygame.mixer.Sound("Alarm.mp3")

    @staticmethod
    def set_alarm(hour, minute):
        AlarmManager.alarm_time = (hour, minute)
        AlarmManager.alarm_active = True
        AlarmManager.is_playing = False

    @staticmethod
    def stop_alarm():
        AlarmManager.alarm_active = False
        AlarmManager.is_playing = False
        if AlarmManager.sound:
            pygame.mixer.stop()

    @staticmethod
    def check_alarm():
        while True:
            if AlarmManager.alarm_active and not AlarmManager.is_playing:
                now = datetime.now()
                if (now.hour, now.minute) == AlarmManager.alarm_time:
                    AlarmManager.trigger_alarm()
            time.sleep(1)  # Check setiap detik

    @staticmethod
    def trigger_alarm():
        try:
            if not AlarmManager.is_playing and AlarmManager.sound:
                AlarmManager.sound.play(-1)  # -1 untuk loop terus menerus
                AlarmManager.is_playing = True
        except Exception as e:
            print(f"Error playing alarm: {e}")

# Deteksi Wajah dan Mata
class WajahVerifier:
    @staticmethod
    def cek_wajah_dan_mata():
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eyes_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        result = False
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            eyes = eyes_cascade.detectMultiScale(roi_gray)
            if len(eyes) >= 1:
                result = True
        cap.release()
        return result

# Soal Matematika
class MathChallenge:
    def __init__(self):
        self.generate()

    def generate(self):
        self.a = random.randint(1, 20)
        self.b = random.randint(1, 20)
        self.pertanyaan = f"{self.a} + {self.b} = ?"
        self.jawaban = str(self.a + self.b)
        return self.pertanyaan

    def cek(self, ans):
        return ans.strip() == self.jawaban

# Halaman Home
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.hour_input = TextInput(hint_text="Jam (0-23)", input_filter='int', multiline=False)
        self.minute_input = TextInput(hint_text="Menit (0-59)", input_filter='int', multiline=False)
        set_button = Button(text="Set Alarm")
        set_button.bind(on_press=self.set_alarm)

        layout.add_widget(Label(text="Set Alarm Time"))
        layout.add_widget(self.hour_input)
        layout.add_widget(self.minute_input)
        layout.add_widget(set_button)
        self.add_widget(layout)

    def set_alarm(self, instance):
        try:
            hour = int(self.hour_input.text)
            minute = int(self.minute_input.text)
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                AlarmManager.set_alarm(hour, minute)
                Thread(target=AlarmManager.check_alarm, daemon=True).start()
                self.manager.current = 'waiting'
            else:
                self.show_popup("Waktu tidak valid.")
        except ValueError:
            self.show_popup("Masukkan angka yang valid.")

    def show_popup(self, message):
        popup = Popup(title="Kesalahan", content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

# Halaman Menunggu
class WaitingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text="Alarm disetel. Menunggu waktu...")
        self.add_widget(self.label)
        self.check_event = None
        
    def on_enter(self):
        # Mulai pengecekan saat screen aktif
        self.check_event = Clock.schedule_interval(self.check_alarm_triggered, 1)
        
    def on_leave(self):
        # Hentikan pengecekan saat pindah screen
        if self.check_event:
            self.check_event.cancel()

    def check_alarm_triggered(self, dt):
        now = datetime.now()
        if AlarmManager.alarm_active and (now.hour, now.minute) == AlarmManager.alarm_time:
            if not AlarmManager.is_playing:
                AlarmManager.trigger_alarm()
            self.manager.current = 'face'
            return False  
        
class FaceVerificationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        self.label = Label(text="Verifikasi wajah... Pastikan mata terbuka.")
        self.img = Image() 
        
        layout.add_widget(self.label)
        layout.add_widget(self.img)
        self.add_widget(layout)
        
        self.cap = None
        self.interval_event = None

    def on_enter(self):
        self.cap = cv2.VideoCapture(0)
        # Update preview lebih sering (30fps)
        self.interval_event = Clock.schedule_interval(self.update_preview, 1.0/30.0)

    def update_preview(self, dt):
        if not self.cap or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        # Konversi frame untuk face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eyes_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Deteksi wajah
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Gambar kotak di sekitar wajah
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            roi_gray = gray[y:y+h, x:x+w]
            
            # Ubah parameter deteksi mata untuk lebih sensitif
            eyes = eyes_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(20, 20)
            )
            
            # Gambar kotak di sekitar mata
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 255, 0), 2)
            
            # Tambahkan counter untuk memastikan mata terdeteksi beberapa frame
            if len(eyes) >= 1:
                if not hasattr(self, 'eye_detected_frames'):
                    self.eye_detected_frames = 0
                self.eye_detected_frames += 1
                
                # Jika mata terdeteksi selama 10 frame berturut-turut
                if self.eye_detected_frames >= 10:
                    self.cleanup() 
                    self.manager.current = 'math'
                    return False 
            else:
                self.eye_detected_frames = 0

        # Konversi frame untuk ditampilkan di Kivy
        buf = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img.texture = texture

    def cleanup(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        if self.interval_event:
            Clock.unschedule(self.interval_event)
        self.interval_event = None

    def on_leave(self):
        self.cleanup()

# Soal Matematika
class MathVerificationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.challenge = MathChallenge()
        layout = BoxLayout(orientation='vertical')
        self.soal = Label(text=self.challenge.pertanyaan)
        self.jawaban = TextInput(hint_text="Jawaban", multiline=False)
        self.submit = Button(text="Submit")
        self.submit.bind(on_press=self.cek_jawaban)

        layout.add_widget(self.soal)
        layout.add_widget(self.jawaban)
        layout.add_widget(self.submit)
        self.add_widget(layout)

    def cek_jawaban(self, instance):
        if self.challenge.cek(self.jawaban.text):
            AlarmManager.stop_alarm()
            self.manager.current = 'done'
        else:
            self.jawaban.text = ''
            self.soal.text = self.challenge.generate()

# Layar Sukses atau Alarm Berhasil Dimatikan
class DoneScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Alarm berhasil dimatikan!"))

# Main App
class AlarmAntiTidurApp(App):
    def build(self):
        AlarmManager.initialize()
        
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(WaitingScreen(name='waiting'))
        sm.add_widget(FaceVerificationScreen(name='face'))
        sm.add_widget(MathVerificationScreen(name='math'))
        sm.add_widget(DoneScreen(name='done'))
        return sm

if __name__ == '__main__':
    AlarmAntiTidurApp().run()
