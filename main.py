import io
import json
import os
import threading
import time
from flask import Flask, Response, send_file
import pyautogui
from PIL import ImageDraw

app = Flask(__name__)

FPS = 60

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
        # pointer_size = 5
        while self.isrunning:
            try:
                screenshot = pyautogui.screenshot()
                if screenshot:
                    # x, y = pyautogui.position()
                    # draw = ImageDraw.Draw(screenshot)
                    # draw.ellipse(
                    #     [x - pointer_size, y- pointer_size, x + pointer_size, y + pointer_size], 
                    #     fill=(255, 0, 0), outline='white'
                    # )
                    img_bytes = io.BytesIO()
                    screenshot.save(img_bytes, format='JPEG')
                    self.last_frame = img_bytes.getvalue()
            except Exception as exc:
                print("Error:", exec)
            time.sleep(delay_time)

    def get_frame(self):
        return self.last_frame

camera = Camera(fps=FPS)
camera.run()

def gen(camera):
    while True:
        frame = camera.get_frame()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(1/ FPS)

@app.route("/blank-video")
def video():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blank.mp4')
    with open(filepath, "rb") as f:
        f_bytes = f.read()
    return send_file(io.BytesIO(f_bytes), mimetype='video/mp4')

@app.route("/stream")
def stream():
    return Response(gen(camera),
        mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/mouse")
def mouse():
    width, height = pyautogui.size()
    def gen_mouse():
        last_x, last_y = 0, 0
        while True:
            x, y = pyautogui.position()
            if last_x != x or last_y != y:
                last_x, last_y = x, y
                data = json.dumps({
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                })
                yield f"""\n{data}"""
            else:
                time.sleep(1 / 144)
    return Response(gen_mouse())
                    

@app.route("/")
def home():
    return """
    <style>
        .img-container {
            position: relative;
            width: 98vw;
            height: 80vh;
        }
        #img {
            position: absolute;
            top: 50%;  
            left: 50%;
            transform: translate(-50%, -50%);
            max-width:100%;
            max-height: 100%;
        }

        #pointer {
            position: absolute;
            width: 15px;
            height: 15px;
        }
    </style>
    <body style="background:black">
        <center>
            <div style="with:0;height:0">
                <video autoplay muted loop>
                    <source src="/blank-video" type="video/mp4">
                </video>
            </div>
            <div id="imgContainer" class="img-container">
                <img id="img" src="/stream" ondblclick="toggleFullscreen()" />
                <div id="pointer">
                    <svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
                        viewBox="0 0 28 28" enable-background="new 0 0 28 28" xml:space="preserve">
                        <polygon fill="#FFFFFF" points="8.2,20.9 8.2,4.9 19.8,16.5 13,16.5 12.6,16.6 "/>
                        <polygon fill="#FFFFFF" points="17.3,21.6 13.7,23.1 9,12 12.7,10.5 "/>
                        <rect x="12.5" y="13.6" transform="matrix(0.9221 -0.3871 0.3871 0.9221 -5.7605 6.5909)" width="2" height="8"/>
                        <polygon points="9.2,7.3 9.2,18.5 12.2,15.6 12.6,15.5 17.4,15.5 "/>
                    </svg>

                </div>
            </div>
        </center>
        <script> 
            var isFullscreen = false;
            var bound;
            var containerBound;
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
                    closeFullscreen(imgContainer)
                } else {
                    openFullscreen(imgContainer)
                }
                isFullscreen = !isFullscreen;

                setTimeout(() => {
                    bound = img.getBoundingClientRect();
                    containerBound = imgContainer.getBoundingClientRect();            
                }, 1000)
            }

            img.onload = () => {
                bound = img.getBoundingClientRect();
                containerBound = imgContainer.getBoundingClientRect();
                fetch("/mouse").then(async (res) => {
                    const reader = res.body.getReader();
                    const textDecoder = new TextDecoder();
                    while (true) {
                        const { done, value } = await reader.read();
                        if (!done) {
                            try{
                                const valText = textDecoder.decode(value).split("\\n").slice(-1)[0].trim()
                                const pos = JSON.parse(valText);
                                // console.log(pos)
                                const posX = bound.left + bound.width * pos.x / pos.width;
                                const posY = bound.top + bound.height * pos.y / pos.height;
                                pointer.style.left = (posX - 3 - containerBound.left) + 'px';
                                pointer.style.top = (posY - 3 - containerBound.top) + 'px';
                            }catch(e){}
                        }
                    }
                })    
            }
            
        </script>
    </body>
    """


def main():
    app.run(host="0.0.0.0", port=9000, threaded=True)
    


if __name__ == "__main__":
    main()