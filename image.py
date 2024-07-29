from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
import io
import base64

app = FastAPI()

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def create_gradient_with_overlay_and_text(size, start_color, end_color, overlay_opacity, text, font_size, line_spacing=1.2):
    # 그라데이션 및 오버레이 생성
    gradient = Image.new('RGB', size)
    draw = ImageDraw.Draw(gradient)
    
    for i in range(size[0]):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / size[0])
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / size[0])
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / size[0])
        draw.line([(i, 0), (i, size[1])], fill=(r, g, b))
    
    overlay = Image.new('RGBA', size, (0, 0, 0, int(255 * overlay_opacity)))
    result = Image.alpha_composite(gradient.convert('RGBA'), overlay)
    result = result.convert('RGB')

    # 텍스트 추가
    draw = ImageDraw.Draw(result)
    font = ImageFont.truetype("/GmarketSansBold.otf", font_size)
    
    # 텍스트 영역 계산 (좌우 5% 여백)
    margin = int(size[0] * 0.05)
    text_width = size[0] - 2 * margin
    
    # 단어 단위 줄바꿈 함수
    def word_wrap(text, width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if draw.textbbox((0, 0), test_line, font=font)[2] <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(' '.join(current_line))
        return lines
    
    wrapped_lines = word_wrap(text, text_width)
    
    # 텍스트 전체 높이 계산 (행간 포함)
    line_height = font.getbbox('A')[3] - font.getbbox('A')[1]
    line_spacing_px = int(line_height * (line_spacing - 1))
    text_height = len(wrapped_lines) * (line_height + line_spacing_px) - line_spacing_px
    
    # 시작 y 좌표 계산 (세로 중앙)
    start_y = (size[1] - text_height) // 2
    
    # 각 줄 개별적으로 중앙 정렬하여 그리기
    for i, line in enumerate(wrapped_lines):
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_width = line_bbox[2] - line_bbox[0]
        x = (size[0] - line_width) // 2
        y = start_y + i * (line_height + line_spacing_px)
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
    
    return result
    

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_image(
    text: str = Form(...),
    start_color: str = Form(...),
    end_color: str = Form(...),
    width: int = Form(...),
    height: int = Form(...)
):
    # 색상 문자열을 RGB 튜플로 변환
    start_rgb = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
    end_rgb = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))

    # 이미지 생성
    image = create_gradient_with_overlay_and_text(
        (width, height), start_rgb, end_rgb, 0.2, text, 30, 1.5
    )

    # 이미지를 바이트 스트림으로 변환
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # 이미지를 base64 인코딩
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()

    return {"image": img_base64}

@app.get("/download")
async def download_image(
    text: str,
    start_color: str,
    end_color: str,
    width: int,
    height: int
):
    # 색상 문자열을 RGB 튜플로 변환
    start_rgb = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
    end_rgb = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))

    # 이미지 생성
    image = create_gradient_with_overlay_and_text(
        (width, height), start_rgb, end_rgb, 0.2, text, 30, 1.5
    )
    # 이미지를 바이트 스트림으로 변환
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return FileResponse(img_byte_arr, media_type="image/png", filename="gradient_image.png")
