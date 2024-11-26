import os
from dotenv import load_dotenv
from io import BytesIO
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from tkinter import font as tkFont
import base64

# env setup and app init
load_dotenv()

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Math Notes - Because Math is Hard")

        self.canvas_width = 1200
        self.canvas_height = 800

        self.canvas = tk.Canvas(root, bg='black', width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        self.root.bind("<Command-z>", self.command_undo)
        self.root.bind("<Return>", self.command_calculate)  # Because hitting Enter feels powerful

        self.last_x, self.last_y = None, None
        self.current_action = []
        self.actions = []

        self.button_clear = tk.Button(root, text="Clear", command=self.clear)
        self.button_clear.pack(side=tk.LEFT)

        self.button_undo = tk.Button(root, text="Undo (Cmd/Ctrl Z)", command=self.undo)
        self.button_undo.pack(side=tk.LEFT)

        self.button_calculate = tk.Button(root, text="Calculate (Return/Enter)", command=self.calculate)
        self.button_calculate.pack(side=tk.LEFT)

        self.custom_font = tkFont.Font(family="Noteworthy", size=100)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("No OpenAI API key. Your math wizard is out of magic.")
        
        self.client = OpenAI(api_key=openai_api_key)

        # draing part kalakari 
    def start_draw(self, event):
        self.current_action = []
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            line_id = self.canvas.create_line((self.last_x, self.last_y, x, y), fill='white', width=5)
            self.draw.line((self.last_x, self.last_y, x, y), fill='white', width=5)
            self.current_action.append((line_id, (self.last_x, self.last_y, x, y)))
        self.last_x, self.last_y = x, y

    def reset(self, event):
        self.last_x, self.last_y = None, None
        if self.current_action:
            self.actions.append(self.current_action)

    #undo and other tools section
    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.actions = []

    def undo(self):
        if self.actions:
            last_action = self.actions.pop()
            for line_id, coords in last_action:
                self.canvas.delete(line_id)
            self.redraw_all()

    def command_undo(self, event):
        self.undo()

    def redraw_all(self):
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.delete("all")
        for action in self.actions:
            for _, coords in action:
                self.draw.line(coords, fill='white', width=5)
                self.canvas.create_line(coords, fill='white', width=5)

    # AI part 
    def calculate(self):
        def encode_image_to_base64(image):
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        base64_image = encode_image_to_base64(self.image)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Solve this math equation and give the answer. Be precise, be brief. I’m looking at you, AI."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}",},
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        answer = response.choices[0].message.content
        self.draw_answer(answer)

    def command_calculate(self, event):
        self.calculate()

    # rendering ais answer as an output 
    def draw_answer(self, answer):
        if not self.actions:
            return
        
        last_action = self.actions[-1]
        last_coords = last_action[-1][-1]

        equals_x = last_coords[2]
        equals_y = last_coords[3]

        x_start = equals_x + 70
        y_start = equals_y - 20

        self.canvas.create_text(x_start, y_start, text=answer, font=self.custom_font, fill="#FF9500")

        font = ImageFont.load_default(size=100)
        self.draw.text((x_start, y_start - 50), answer, font=font, fill="#FF9500")


if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()