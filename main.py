import io
import threading
import time
from flask import Flask, Response, send_file
import pyautogui
from PIL import ImageDraw

app = Flask(__name__)

class Camera:
    def __init__(self,fps=60):
        self.fps = fps
        self.last_frame = None
        self.isrunning = False
        self.thread = None
        
    def run(self):
        if self.thread is None:
            thread = threading.Thread(target=self._capture_loop,daemon=True)
            self.isrunning = True
            thread.start()

    def _capture_loop(self):
        delay_time = 1/self.fps
        poiter_size = 5
        while self.isrunning:
            screenshot = pyautogui.screenshot()
            x, y = pyautogui.position()

            if screenshot:
                draw = ImageDraw.Draw(screenshot)
                draw.ellipse(
                    [x - poiter_size, y- poiter_size, x + poiter_size, y + poiter_size], 
                    fill=(0, 0, 0), outline='white'
                )
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='JPEG')
                self.last_frame = img_bytes.getvalue()
            time.sleep(delay_time)

    def get_frame(self):
        return self.last_frame

camera = Camera()
camera.run()

def gen(camera):
    fps = 60
    while True:
        frame = camera.get_frame()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(1/ fps)

@app.route("/blank-video")
def video():
    with open("blank.mp4", "rb") as f:
        f_bytes = f.read()
    return send_file(io.BytesIO(f_bytes), mimetype='video/mp4')

@app.route("/stream")
def stream():
    return Response(gen(camera),
        mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def home():
    return """
    <body style="background:black">
        <center>
            <div style="display:none">
                <video controls autoplay muted loop>
                    <source src="/blank-video" type="video/mp4">
                </video>
            </div>
            <img id="img" style="max-width:99vw;max-height:80vh;" src="/stream" ondblclick="toggleFullscreen()" />
        </center>
        <script> 
            var isFullscreen = false;
            function openFullscreen(elem) {
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) { /* Safari */
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) { /* IE11 */
                    elem.msRequestFullscreen();
                }
            }

            /* Close fullscreen */
            function closeFullscreen(elem) {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) { /* Safari */
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) { /* IE11 */
                    document.msExitFullscreen();
                }
            }

            function toggleFullscreen(){
                if(isFullscreen){
                    closeFullscreen(img)
                } else {
                    openFullscreen(img)
                }
                isFullscreen = !isFullscreen;
            }
        </script>
    </body>
    """


def main():
    app.run(host="0.0.0.0", port=9000, threaded=True)
    


if __name__ == "__main__":
    main()