from util.crash_reporter import install_crash_reporting

install_crash_reporting()

from app.app import SpotOnSightApp

if __name__ == "__main__":
    SpotOnSightApp().run()
