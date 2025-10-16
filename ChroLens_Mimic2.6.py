#Set-Location 'c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic'; python .\ChroLens_Mimic2.6.py
from recorder_app import RecorderApp

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()