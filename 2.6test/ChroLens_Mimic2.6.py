#pyinstaller --noconsole --onedir --icon=umi_奶茶色.ico --add-data "umi_奶茶色.ico;." ChroLens_Mimic2.6.py
#pyinstaller --onedir --console --icon=umi_奶茶色.ico --add-data "umi_奶茶色.ico;." --add-data "pic;pic" --add-data "scripts;scripts" --add-data "TTF;TTF" --add-data "user_config.json;." ChroLens_Mimic2.6.py
#Set-Location 'c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic'; python .\ChroLens_Mimic2.6.py
from recorder_app import RecorderApp

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()
