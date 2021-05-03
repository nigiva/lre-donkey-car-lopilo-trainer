import tkinter as tk
from tqdm import tqdm
import pandas as pd
from PIL import Image, ImageTk
import os
import keyboard
import json
from io import BytesIO
import base64
from time import time

# Constantes
ESLR_PATH = "/home/nigiva/git/lopilo-trainer/data/sample/extern/corentin_renault_20000_record_controller.eslr"
EXTRACT_PATH = "/home/nigiva/git/lopilo-trainer/data/sample/extern/corentin_renault_20000_record_controller"


# To avoid error Display not found in Visual Code
if os.environ.get('DISPLAY','') == '':
    os.environ.__setitem__('DISPLAY', ':1')


class ESLRExtractor:
  def __init__(self, eslr_path):
    self.eslr_path = eslr_path
    if not os.path.exists(self.eslr_path):
      raise Exception("ESLR File not found !")
  
  def extract(self, label_path, images_path, image_ext = ".jpeg"):
    #Check if extracted files already exist
    if os.path.exists(label_path) and os.path.exists(images_path):
        print("[WARNING] Extracted files already exist")
        return
    
    # Créer le dossier qui contiendra toutes les images extraites du .eslr s'il n'existe pas
    os.makedirs(images_path, exist_ok=True)

    # Ouvrir le fichier label.csv
    label_file = open(label_path, "w")

    # Pour définir les en-têtes du fichier label, il faut lire au moins la première ligne
    # du fichier *.eslr
    label_head_is_defined = False

    # Lire le fichier eslr
    with open(self.eslr_path, "r") as dataset_file:
      for i, line in enumerate(tqdm(dataset_file)):
        data_line = json.loads(line)
        if (data_line["msg_type"] == "telemetry"):
          # Si le header n'a pas encore initialisé
          if not label_head_is_defined:
            label_head_list = list(data_line.keys())
            label_head_list.remove("msg_type")
            label_head_list.remove("image")
            label_head_list = ['path'] + label_head_list
            label_head_str = ",".join(label_head_list)
            # Écrire le header dans le CSV
            label_file.write(label_head_str + "\n")
            label_head_is_defined = True
          # Définir le path de l'image à enregistrer
          image_focused_path = os.path.join(images_path, str(i) + image_ext)
          data_line['path'] = image_focused_path
          # Lire, décoder et enregistrer l'image
          Image.open(BytesIO(base64.b64decode(data_line["image"]))).save(image_focused_path)
          # Ajouter toutes les données de la ligne lue dans un le CSV
          # Mettre 0 comme valeur par défaut si la valeur n'est pas trouvée dans data_line
          data_list_to_write = [str(data_line.get(k, 0)) for k in label_head_list]
          label_file.write(",".join(data_list_to_write) + "\n")
    label_file.close()
  
  @staticmethod
  def read_csv(csv_path):
    return pd.read_csv(csv_path)

class DatasetSpliterUI:
    def __init__(self, data_to_show, refresh_delay = 15):
        self.window = tk.Tk()
        self.window.title("Dataset Spliter")

        self.refresh_delay = refresh_delay

        self.data_to_show = data_to_show
        self.data_to_show['label'] = "E"

        self.index = 0

        self.key_press = dict()

        self.draw_ui()

    def draw_ui(self):
        self.howitworks_text = tk.StringVar()
        howitworks_string = 'Directional arrows to change image\n' + '"E" / "R" key to add a label\n' + 'Enter to finish'
        self.howitworks_text.set(howitworks_string)
        self.howitworks_label = tk.Label(self.window, textvariable=self.howitworks_text)
        self.howitworks_label.pack(side = "top") 
        
        self.image_label = tk.Label(self.window)
        self.image_label.pack(side = "top")


        self.label_text = tk.StringVar()
        self.label_text.set("Label = NONE")
        self.label_label = tk.Label(self.window, textvariable=self.label_text)
        self.label_label.configure(font=("Courier", 16, "bold"))
        self.label_label.pack(side = "top")

        self.description_text = tk.StringVar()
        self.description_text.set("Description")
        self.description_label = tk.Label(self.window, textvariable=self.description_text)
        self.description_label.pack(side = "bottom")

        self.window.bind('<KeyPress>', self.key_press_event)
        self.window.bind('<KeyRelease>', self.key_release_event)
        
        self.refresh_ui()
        self.key_listener()
        self.window.mainloop()

    def refresh_ui(self):
        data_line = self.get_line_in_data()
        #print(data_line)
        data_line_dict = data_line.to_dict()
        description = ""
        for key, value in data_line_dict.items():
            if key == "path":
                description += str(key) + " = " + os.path.basename(str(value)) + "\n"
            elif key == "label":
                self.label_text.set("LABEL = " + str(value))
            description += str(key) + " = " + str(value) + "\n"
        self.description_text.set(description)

        self.image = Image.open(data_line['path'])
        imagetk = ImageTk.PhotoImage(image=self.image)
        self.image_label.config(image=imagetk)
        self.image_label.image = imagetk

        self.window.update_idletasks()

    def get_line_in_data(self):
        return self.data_to_show.iloc[self.index]

    def key_listener(self):
        #print(self.key_press)
        for k, s in self.key_press.items():
            if k == "Left" and s and self.index != 0:
                self.index -= 1
            if k == "Right" and s and self.index != len(self.data_to_show) - 1:
                self.index += 1
            if k == "e" and s:
                self.data_to_show.at[self.index, "label"] = "E"
            if k == "r" and s:
                self.data_to_show.at[self.index, "label"] = "R"
            if k == "Return" and s:
                self.close()
                return
        self.refresh_ui()
        self.window.after(self.refresh_delay, self.key_listener)
    
    def key_press_event(self, event):
        self.key_press[event.keysym] = True
            
    def key_release_event(self, event):
        self.key_press[event.keysym] = False
    
    def close(self):
        data_e = self.data_to_show[self.data_to_show.label == "E"]
        data_r = self.data_to_show[self.data_to_show.label == "R"]
        t = str(time())
        with open("e-" + t + ".eslr", "w") as f:
            for i, r in tqdm(data_e.iterrows()):
                path = r["path"]
                img = Image.open(path)
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue())
                del(r["path"])
                r["msg_type"] = "telemetry"
                r["image"] = img_str
                f.write(r.to_json())
                f.write("\n")

        with open("r-" + t + ".eslr", "w") as f:
            for i, r in tqdm(data_r.iterrows()):
                path = r["path"]
                img = Image.open(path)
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue())
                del(r["path"])
                r["msg_type"] = "telemetry"
                r["image"] = img_str
                f.write(r.to_json())
                f.write("\n")
        
        self.window.destroy()

extractor = ESLRExtractor(ESLR_PATH)
extractor.extract(label_path = os.path.join(EXTRACT_PATH, "label.csv"),
                images_path = os.path.join(EXTRACT_PATH, "images"),
                image_ext = ".jpeg"
                )

data = extractor.read_csv(os.path.join(EXTRACT_PATH, "label.csv"))
UI = DatasetSpliterUI(data_to_show = data)