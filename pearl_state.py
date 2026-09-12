import time
from datetime import datetime
from enum import Enum, auto

class PearlState(Enum):
    IDLE = auto()
    FEEDING = auto()
    PLAYING = auto()
    STUDYING = auto()
    DISTRESSED = auto()

class Pearl:
    """
    State machine and stats controller for Pearl the Pixelated Jaguar.
    Manages state timers, stats, real-time schedule slowdowns, and in-game text messages.
    """
    def __init__(self, name="Pearl"):
        self.name = name
        self.state = PearlState.IDLE
        
        # Stats (0 to 100)
        self.hunger = 80      # 100 = Full, 0 = Starving
        self.happiness = 75   # 100 = Delighted, 0 = Depressed
        self.grades = 65      # 100 = Straight A's, 0 = Failing
        
        # Time Acceleration Multiplier (1x, 2x, 5x, 10x)
        self.time_scale = 1.0
        
        # Timers
        self.activity_timer = 0.0
        self.idle_timer = 0.0
        self.decay_timer = 0.0
        self.anim_tick_timer = 0.0
        self.anim_frame = 0

        # Activity duration in seconds
        self.ACTIVITY_DURATION = 4.0

        # Track Monday reset state
        self.last_monday_reset_day = None

        # Current dialogue message displayed in the bottom text box inside the game
        self._update_idle_message()

    def get_schedule_status(self):
        """
        Returns real-time schedule info: is_night (7 PM to 7 AM), is_weekend, is_monday, decay_multiplier
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0=Mon, 5=Sat, 6=Sun

        is_night = (hour >= 19 or hour < 7)  # 7:00 PM to 7:00 AM
        is_weekend = (weekday in (5, 6))
        is_monday = (weekday == 0)

        if is_night:
            decay_multiplier = 0.2  # 80% slowdown overnight (Pearl sleeping)
        elif is_weekend:
            decay_multiplier = 0.02  # Ultra-slow burn over weekend (~63 hours to distressed)
        else:
            decay_multiplier = 1.0

        return {
            "is_night": is_night,
            "is_weekend": is_weekend,
            "is_monday": is_monday,
            "decay_multiplier": decay_multiplier,
        }

    def cycle_time_speed(self):
        """
        Cycles time acceleration multiplier between 1x, 2x, 5x, and 10x.
        """
        speeds = [1.0, 2.0, 5.0, 10.0]
        idx = (speeds.index(self.time_scale) + 1) % len(speeds) if self.time_scale in speeds else 0
        self.time_scale = speeds[idx]
        self.current_message = f"⚡ Game Speed set to {self.time_scale:g}x!"
        return self.time_scale

    def feed(self):
        if self.state in (PearlState.FEEDING, PearlState.PLAYING, PearlState.STUDYING):
            self.current_message = f"Pearl is busy right now!"
            return False
        
        self.state = PearlState.FEEDING
        self.activity_timer = self.ACTIVITY_DURATION
        self.anim_tick_timer = 0.0
        self.anim_frame = 0
        
        # Overfeeding check: Allow hunger up to 125%; trigger 'too full' overfed state at >= 125%
        new_hunger = self.hunger + 25
        if new_hunger >= 125 or self.hunger >= 125:
            self.hunger = min(125, max(self.hunger, new_hunger))
            self.happiness = max(0, self.happiness - 10)
            self.current_message = f"Pearl is stuffed and too full to eat! Overfeeding reduced her happiness."
        elif new_hunger >= 100:
            self.hunger = new_hunger
            self.current_message = f"Offered a meal to {self.name}! She is full and content."
        else:
            self.hunger = new_hunger
            self.current_message = f"Offered a meal to {self.name}!"
        return True

    def play(self):
        if self.state in (PearlState.FEEDING, PearlState.PLAYING, PearlState.STUDYING):
            self.current_message = f"Pearl is busy right now!"
            return False

        self.state = PearlState.PLAYING
        self.activity_timer = self.ACTIVITY_DURATION
        self.anim_tick_timer = 0.0
        self.anim_frame = 0
        
        # Update stats
        self.happiness = min(100, self.happiness + 20)
        self.hunger = max(0, self.hunger - 5)
        self.current_message = f"Tossed a ball for {self.name}!"
        return True

    def study(self):
        if self.state in (PearlState.FEEDING, PearlState.PLAYING, PearlState.STUDYING):
            self.current_message = f"Pearl is busy right now!"
            return False

        self.state = PearlState.STUDYING
        self.activity_timer = self.ACTIVITY_DURATION
        self.anim_tick_timer = 0.0
        self.anim_frame = 0
        
        # Update stats
        self.grades = min(100, self.grades + 15)
        self.happiness = max(0, self.happiness - 3)
        self.current_message = f"Hitting the books with {self.name}!"
        return True

    def update(self, dt: float):
        """
        Advances the state machine and updates in-game dialogue text messages.
        Accelerated by self.time_scale and slowed by real-time schedule rules.
        """
        scaled_dt = dt * self.time_scale
        sched = self.get_schedule_status()

        # Handle Monday Reset (trigged on Monday morning for a new academic week)
        today_str = datetime.now().strftime("%Y-%m-%d")
        if sched["is_monday"] and self.last_monday_reset_day != today_str:
            self.last_monday_reset_day = today_str
            self.grades = max(80, self.grades)  # Reset grades to 80% baseline for new school week
            self.hunger = max(75, self.hunger)
            self.happiness = max(75, self.happiness)
            self.current_message = f"Happy Monday! A new academic week starts – Pearl's grades & stats refreshed!"

        # Periodic stat decay (every 4 minutes / 240 seconds, modified by night/weekend slowdown)
        self.decay_timer += scaled_dt * sched["decay_multiplier"]
        if self.decay_timer >= 240.0:
            self.decay_timer = 0.0
            self.hunger = max(0, self.hunger - 3)
            self.happiness = max(0, self.happiness - 2)
            self.grades = max(0, self.grades - 2)

        # Handle Active States (FEEDING, PLAYING, STUDYING)
        if self.state in (PearlState.FEEDING, PearlState.PLAYING, PearlState.STUDYING):
            self.activity_timer -= scaled_dt
            self.anim_tick_timer += scaled_dt

            # Animation frame tick every ~0.8s
            if self.anim_tick_timer >= 0.8:
                self.anim_tick_timer = 0.0
                self.anim_frame += 1
                self._update_activity_message()

            # Check if activity finished
            if self.activity_timer <= 0:
                self.current_message = f"{self.name} finished and feels great!"
                self.state = PearlState.IDLE
                self.idle_timer = 0.0

        # Handle Idle & Distressed Check
        else:
            # Check if Pearl is distressed due to low stats (< 25)
            is_low = self.hunger < 25 or self.happiness < 25 or self.grades < 25
            if is_low:
                if self.state != PearlState.DISTRESSED:
                    self.state = PearlState.DISTRESSED
                    self._update_distressed_message()

                self.idle_timer += scaled_dt
                if self.idle_timer >= 3.0:
                    self.idle_timer = 0.0
                    self._update_distressed_message()
            else:
                if self.state == PearlState.DISTRESSED:
                    self.state = PearlState.IDLE
                    self.current_message = f"{self.name} recovered and feels better!"
                
                self.idle_timer += scaled_dt
                if self.idle_timer >= 4.0:
                    self.idle_timer = 0.0
                    self._update_idle_message()

    def _update_distressed_message(self):
        distressed_reasons = []
        if self.hunger < 25:
            distressed_reasons.append("Pearl is starving and needs food!")
        if self.happiness < 25:
            distressed_reasons.append("Pearl is lonely and sad!")
        if self.grades < 25:
            distressed_reasons.append("Pearl is stressed about her failing grades!")
        
        if distressed_reasons:
            self.current_message = distressed_reasons[int(time.time()) % len(distressed_reasons)]

    def _update_activity_message(self):
        if self.state == PearlState.FEEDING:
            if self.hunger >= 125:
                messages = [
                    f"*groans* Pearl holds her stuffed belly...",
                    f"Too full! Pearl turns her head away from the food...",
                    f"Pearl rubs her overfilled tummy uncomfortably...",
                    f"Pearl needs play time or study to digest!"
                ]
            else:
                messages = [
                    f"*sniff sniff* inspects the meat...",
                    f"*CHOMP CHOMP* munching happily!",
                    f"*gulp* licking whiskers... mmm!",
                    f"Purring with a satisfied belly!"
                ]
            self.current_message = messages[self.anim_frame % len(messages)]

        elif self.state == PearlState.PLAYING:
            messages = [
                f"Crouches low, wiggling tail...",
                f"POUNCE! Jaguar leap in mid-air!",
                f"Rolls over with the toy ball!",
                f"Zoomies around the room!"
            ]
            self.current_message = messages[self.anim_frame % len(messages)]

        elif self.state == PearlState.STUDYING:
            messages = [
                f"Adjusts glasses, reading closely...",
                f"*flips page* taking notes with a paw!",
                f"Lightbulb moment! Eureka!",
                f"Writing python code on the screen!"
            ]
            self.current_message = messages[self.anim_frame % len(messages)]

    def _update_idle_message(self):
        sched = self.get_schedule_status()
        if sched["is_night"]:
            idle_messages = [
                f"Pearl is sleeping soundly... Zzz",
                f"Pearl is curled up in her warm bed resting...",
                f"Nighttime in the jungle... Pearl is dreaming quietly...",
            ]
        elif sched["is_weekend"]:
            idle_messages = [
                f"Pearl is enjoying a cozy weekend nap in her favorite spot...",
                f"Pearl stretches her paws lazily, soaking in the quiet weekend...",
                f"Pearl swishes her tail happily, taking a well-deserved weekend break...",
                f"Pearl is purring softly, dreaming of peaceful weekend adventures...",
            ]
        else:
            idle_messages = [
                f"Pearl is lounging gracefully on her branch...",
                f"Pearl swishes her spotted tail lazily...",
                f"Pearl blinks her amber eyes and looks around...",
                f"Pearl lets out a gentle, quiet purr...",
            ]
        self.current_message = idle_messages[int(time.time()) % len(idle_messages)]
