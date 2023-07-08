import gi, os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import pickle, json, shutil
from gi.repository import Gtk, Adw, Gio


class Extension(Gtk.Window):
    def __init__(self,app):
        Gtk.Window.__init__(self, title="Extensions")
        self.path = os.path.expanduser("~")+"/.var/app/io.github.qwersyk.Newelle/extension"

        self.app = app
        self.set_default_size(500, 500)
        self.set_transient_for(app.win)
        self.set_modal(True)
        self.set_titlebar(Adw.HeaderBar(css_classes=["flat"]))

        self.notification_block = Adw.ToastOverlay()
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.notification_block.set_child(self.scrolled_window)

        self.set_child(self.notification_block)
        self.update()
    def update(self):
        self.main = Gtk.Box(margin_top=10,margin_start=10,margin_bottom=10,margin_end=10,valign=Gtk.Align.START,halign=Gtk.Align.CENTER,orientation=Gtk.Orientation.VERTICAL)
        self.main.set_size_request(300, -1)
        self.scrolled_window.set_child(self.main)
        if os.path.exists(self.path):
            folder_names = [name for name in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, name))]
            for name in folder_names:
                main_json_path = os.path.join(self.path, name, "main.json")
                if os.path.exists(main_json_path):
                    with open(main_json_path, "r") as file:
                        main_json_data = json.load(file)
                        box = Gtk.Box(margin_top=10,margin_start=10,margin_end=10,margin_bottom=10,css_classes=["card"])
                        box.append(Gtk.Label(label=f"{name}",margin_top=10,margin_start=10,margin_end=10,margin_bottom=10))
                        box_elements = Gtk.Box(valign=Gtk.Align.CENTER,halign=Gtk.Align.END, hexpand= True)
                        button = Gtk.Button(css_classes=["flat"], margin_top=10,margin_start=10,margin_end=10,margin_bottom=10)
                        button.connect("clicked", self.delete_extension)
                        button.set_name(name)

                        icon_name="user-trash-symbolic"
                        icon = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name=icon_name))
                        icon.set_icon_size(Gtk.IconSize.INHERIT)
                        button.set_child(icon)
                        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
                        switch.connect("notify::state", self.change_status)
                        switch.set_name(name)
                        if main_json_data.get("status"):
                            switch.set_active(True)
                        box_elements.append(switch)
                        box_elements.append(button)
                        box.append(box_elements)
                        self.main.append(box)
        folder_button = Gtk.Button(label="Choose an extension",margin_top=10,margin_start=10,margin_bottom=10,margin_end=10,css_classes=["flat"])
        folder_button.connect("clicked", self.on_folder_button_clicked)
        self.main.append(folder_button)
    def change_status(self,widget,*a):
        status = False
        name = widget.get_name()
        if widget.get_active():
            status = True
        with open(os.path.join(os.path.join(self.path, name), "main.json"), "r") as file:
            main_json_data = json.load(file)
        main_json_data["status"] = status
        if name in self.app.win.extensions:
            self.app.win.extensions[name]["status"]=status
        with open(os.path.join(os.path.join(self.path, widget.get_name()), "main.json"), "w") as file:
            json.dump(main_json_data, file)
    def delete_extension(self,widget):
        folder_path = os.path.join(self.path, widget.get_name())
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            self.notification_block.add_toast(Adw.Toast(title=(f'The "{widget.get_name()}" extension has been removed')))
        self.update()
    def on_folder_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(transient_for=self.app.win, title=_("Open Model"), modal=True, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL, _("Open"), Gtk.ResponseType.ACCEPT)
        dialog.connect("response", self.process_folder)
        dialog.present()
    def process_folder(self, dialog, response):
        if response != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return False

        file=dialog.get_file()
        if file == None:
            return True
        folder_path = file.get_path()
        main_json_path = os.path.join(folder_path, "main.json")
        if os.path.isfile(main_json_path):
            with open(main_json_path, "r") as file:
                main_json_data = json.load(file)
                name = main_json_data.get("name")
                prompt = main_json_data.get("prompt")
                api = main_json_data.get("api")
                about = main_json_data.get("about")

            if name and about and prompt and api:
                new_folder_path = os.path.join(self.path, name)
                if os.path.exists(new_folder_path):
                    shutil.rmtree(new_folder_path)

                shutil.copytree(folder_path, new_folder_path)
                self.notification_block.add_toast(Adw.Toast(title=(f"Extension added. New extensions will run from the next launch")))
                main_json_data["status"] = False

                with open(os.path.join(new_folder_path, "main.json"), "w") as file:
                    json.dump(main_json_data, file)
                self.update()
            else:
                self.notification_block.add_toast(Adw.Toast(title='The extension is wrong'))
        else:
            self.notification_block.add_toast(Adw.Toast(title="This is not an extension"))

        dialog.destroy()
        return False
