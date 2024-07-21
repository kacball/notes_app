from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.button import Button
from kivy.storage.jsonstore import JsonStore
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.slider import Slider
from kivy.core.window import Window
import datetime
import json

store = JsonStore('siema.json')
Window.clearcolor = (0/255, 51/255, 102/255, 1)

class Note:
    def __init__(self, text, importance=1, note_datetime=None):
        self.text = text
        self.importance = importance
        self.note_datetime = note_datetime if note_datetime else str(datetime.datetime.now())

    def long(self):
        long_box = BoxLayout(orientation='vertical')
        long_box.add_widget(Label(text="Importance: " + str(self.importance) + "/7"))
        long_box.add_widget(Label(text=str(self.note_datetime)))
        long_box.add_widget(Label(text=self.text))
        return long_box

    def short(self):
        return Button(text=(self.text[:25] + '...' if len(self.text) > 25 else self.text) + " " + str(self.importance) + "/7", on_press=self.show_detail)

    def show_detail(self):
        store.put("current_note", text=self.text, importance=self.importance, note_datetime=self.note_datetime)
        notes_app.screen_manager.current = "past_note"

    def to_json(self):
        return json.dumps(self.__dict__)

class RV(RecycleView):
    def __init__(self):
        super().__init__()

class HistoryList(Screen):
    def __init__(self, **kwargs):
        super(HistoryList, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.sort_by = 'date'
        self.build_ui()

    def build_ui(self):
        sort_buttons = BoxLayout(size_hint_y=0.1, spacing=10)
        sort_by_date_button = Button(text="Sort by Date", background_color = ((204/255, 0, 102/255, 1)))
        sort_by_date_button.bind(on_press=lambda x: self.sort_notes('date'))
        sort_by_importance_button = Button(text="Sort by Importance", background_color = (204/255, 0, 102/255, 1))
        sort_by_importance_button.bind(on_press=lambda x: self.sort_notes('importance'))
        sort_buttons.add_widget(sort_by_date_button)
        sort_buttons.add_widget(sort_by_importance_button)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(sort_buttons)
        
        self.rv = RV()
        self.rv.spacing = 20
        self.refresh_notes()
        layout.add_widget(self.rv)
        self.add_widget(layout)

    def on_enter(self):
        self.refresh_notes()

    def refresh_notes(self):
        notes_list = store.get("notes_list")["notes_list"]
        notes = [Note(**json.loads(note)) for note in notes_list]

        if self.sort_by == 'date':
            notes.sort(key=lambda x: x.note_datetime, reverse=True)
        elif self.sort_by == 'importance':
            notes.sort(key=lambda x: (x.importance, x.note_datetime), reverse=True)

        self.rv.data = [{'text': "Back", 'on_press': self.go_back, 'background_color' : (1, 1, 0, 1)}]
        for note in notes:
            self.rv.data.append({'text': note.short().text, 'on_press': note.show_detail, 'background_color' : (0, 0.8, 1, 1)})

    def sort_notes(self, criteria):
        self.sort_by = criteria
        self.refresh_notes()

    def go_back(self):
        notes_app.screen_manager.current = "new_note"

class PastNoteScreen(Screen):
    def __init__(self, **kwargs):
        super(PastNoteScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        layout = BoxLayout(orientation='vertical')
        self.note_label = Label(text="chuj")
        self.update_note_label()
        layout.add_widget(self.note_label)
        button_box = BoxLayout(size_hint_y=0.1)
        back_button = Button(text="Back", background_color=(0.7, 0.4, 1, 1))
        back_button.bind(on_press=self.go_back)
        button_box.add_widget(back_button)
        layout.add_widget(button_box)
        self.add_widget(layout)

    def on_pre_enter(self, *args):
        # This method is called before the screen is shown
        self.update_note_label()

    def update_note_label(self):
        if store.exists("current_note"):
            note = store.get("current_note")
            text = note["text"]
            importance = note["importance"]
            note_datetime = note["note_datetime"]
            self.note_label.text = f"Note:\n {text}\nImportance: {importance}/7\nDate: {note_datetime}"
        else:
            self.note_label.text = "No note to display."

    def go_back(self, instance):
        notes_app.screen_manager.current = "history_list"

class ImportanceSlider(BoxLayout):
    def __init__(self, **kwargs):
        super(ImportanceSlider, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.importance_slider = Slider(min=1, max=7, step=1, value=1)
        label_box = BoxLayout(size_hint_y = 0.05)
        self.importance_label = Label(text="Importance: 1/7")
        self.importance_slider.bind(value=self.update_label)
        label_box.add_widget(self.importance_label)
        self.add_widget(label_box)
        self.add_widget(self.importance_slider)

    def update_label(self, instance, value):
        self.importance_label.text = f"Importance: {int(value)}/7"

class NewNoteScreen(Screen):
    def __init__(self, **kwargs):
        super(NewNoteScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        layout = BoxLayout(size_hint_y = 0.3, orientation='vertical')
        layout.add_widget(Label(text="New note"))
        self.importance_slider = ImportanceSlider()
        layout.add_widget(self.importance_slider)
        # self.add_widget(layout)

        text_layout = BoxLayout()
        self.text_field = TextInput(multiline=True)
        text_layout.add_widget(self.text_field)
        # self.add_widget(text_layout)

        big_layout = BoxLayout(orientation='vertical')
        big_layout.add_widget(layout)
        big_layout.add_widget(text_layout)
        self.add_widget(big_layout)

        button_layout = BoxLayout(size_hint_y=0.15)
        save_button = Button(text="Save Note", background_color=(0.5, 0.9, 0.5, 1))
        save_button.bind(on_press=self.save_note)
        history_button = Button(text="View History", background_color=(0.9, 0.5, 0.5, 1))
        history_button.bind(on_press=self.view_history)
        button_layout.add_widget(save_button)
        button_layout.add_widget(history_button)
        self.add_widget(button_layout)

        self.load_draft()

    def save_note(self, instance):
        text = self.text_field.text
        if text != "":
            importance = int(self.importance_slider.importance_slider.value)
            new_note = Note(text=text, importance=importance)
            notes_list = store.get("notes_list")["notes_list"]
            notes_list.append(new_note.to_json())
            store.put("notes_list", notes_list=notes_list)
            self.text_field.text = ''
            self.importance_slider.importance_slider.value = 1  # Reset slider
            self.clear_draft()

    def view_history(self, instance):
        notes_app.screen_manager.current = "history_list"

    def save_draft(self):
        draft_text = self.text_field.text
        draft_importance = int(self.importance_slider.importance_slider.value)
        store.put("draft_note", text=draft_text, importance=draft_importance)

    def load_draft(self):
        if store.exists("draft_note"):
            draft = store.get("draft_note")
            self.text_field.text = draft.get("text", "")
            self.importance_slider.importance_slider.value = draft.get("importance", 1)

    def clear_draft(self):
        if store.exists("draft_note"):
            store.delete("draft_note")

class NotesApp(App):
    def build(self):
        self.screen_manager = ScreenManager()

        if not store.exists("notes_list"):
            store.put("notes_list", notes_list=[])

        self.new_note_screen = NewNoteScreen(name="new_note")
        self.history_list = HistoryList(name="history_list")
        self.past_note_screen = PastNoteScreen(name="past_note")

        self.screen_manager.add_widget(self.new_note_screen)
        self.screen_manager.add_widget(self.history_list)
        self.screen_manager.add_widget(self.past_note_screen)

        return self.screen_manager

    def on_stop(self):
        # Save the draft note when the app is closed
        self.new_note_screen.save_draft()

notes_app = NotesApp()
notes_app.run()
