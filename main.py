import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import easyocr
import cv2
import numpy as np
import re

# OCR 초기화
reader = easyocr.Reader(['ko', 'en'])

# 이미지 전처리
def preprocess_image(image_path):
    pil_img = Image.open(image_path).convert("RGB")
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    return enhanced

# OCR 정보 추출
def extract_info(image_path):
    preprocessed = preprocess_image(image_path)
    results = reader.readtext(preprocessed, detail=0)
    print("OCR 결과:", results)

    info = {
        '이름': None,
        '주민등록번호': None,
        '주소': None,
        '발행일': None,
        '발행지역': None
    }

    address_parts = []

    for i, line in enumerate(results):
        line = line.strip()

        # 주민등록번호
        if re.search(r"\d{6}-\d{7}", line):
            info['주민등록번호'] = line
            if i > 0:
                prev_line = results[i - 1].strip()
                if "주민등록증" not in prev_line:
                    prev_line = re.sub(r"\(.*?\)", "", prev_line)  # 괄호 제거
                    info['이름'] = prev_line.strip()

        # 발행일 (조합: 연도, 월, 일 세 줄)
        if i < len(results) - 2:
            if results[i].isdigit() and len(results[i]) == 4:  # 연도
                if results[i+1].isdigit():
                    if re.match(r"\d{1,2}\.?$", results[i+2]):
                        info['발행일'] = f"{results[i]}.{results[i+1]}.{results[i+2].replace('.', '')}"

        # 발행지역
        if "청장" in line:
            info['발행지역'] = line

        # 주소 (발행지역 제외)
        elif any(word in line for word in ["시", "구", "동", "호"]):
            if "청장" not in line:  # 발행지역은 주소에 포함하지 않음
                address_parts.append(line)

    if address_parts:
        info['주소'] = " ".join(address_parts)

    return info

# GUI 클래스
class ResidentCardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("주민등록증 정보 추출기")
        self.root.geometry("1200x700")

        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽 이미지 영역 (Canvas로 크게 표시)
        self.canvas = tk.Canvas(main_frame, width=500, height=600, bg="lightgray")
        self.canvas.grid(row=0, column=0, rowspan=6, padx=20, pady=20)

        # 오른쪽 정보 필드
        labels = ['이름', '주민등록번호', '주소', '발행일', '발행지역']
        self.fields = {}
        for i, label in enumerate(labels):
            tk.Label(main_frame, text=label, width=12, anchor='w', font=("Arial", 12)).grid(row=i, column=1, padx=10, pady=10, sticky="w")
            if label == "주소":
                entry = tk.Text(main_frame, width=50, height=3, font=("Arial", 12))
                entry.grid(row=i, column=2, padx=10, pady=10, sticky="w")
            else:
                entry = tk.Entry(main_frame, width=50, font=("Arial", 12))
                entry.grid(row=i, column=2, padx=10, pady=10, sticky="w")
            self.fields[label] = entry

        # 오른쪽 하단 업로드 버튼
        self.upload_btn = tk.Button(main_frame, text="이미지 업로드", command=self.load_image, font=("Arial", 12), bg="lightblue")
        self.upload_btn.grid(row=5, column=2, padx=10, pady=20, sticky="e")

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            img = Image.open(file_path)
            img = img.resize((500, 600))  # 크게 표시
            img_tk = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
            self.canvas.image = img_tk  # 이미지 유지

            info = extract_info(file_path)
            for key in self.fields:
                if key == "주소":
                    self.fields[key].delete("1.0", tk.END)
                    self.fields[key].insert("1.0", info.get(key, ""))
                else:
                    self.fields[key].delete(0, tk.END)
                    self.fields[key].insert(0, info.get(key, ""))

def run_app():
    root = tk.Tk()
    app = ResidentCardApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()