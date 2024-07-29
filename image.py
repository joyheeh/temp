import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

def create_gradient_with_overlay_and_text(size, start_color, end_color, overlay_opacity, text, font_size, line_spacing=1.2, margin_percent=5):
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
    try:
        font_path = os.path.join(os.path.dirname(__file__), "GmarketSansBold.otf")
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        st.warning("Custom font not found. Using default font.")
        font = ImageFont.load_default()
    
    # 텍스트 영역 계산 (사용자 지정 여백)
    margin = int(size[0] * (margin_percent / 100))
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

# Streamlit app
st.title("Gradient Image Generator")

# Input fields
text = st.text_area("Enter text for the image")
start_color = st.color_picker("Select start color", "#000000")
end_color = st.color_picker("Select end color", "#FFFFFF")
width = st.number_input("Image width", min_value=100, max_value=2000, value=800)
height = st.number_input("Image height", min_value=100, max_value=2000, value=400)
font_size = st.number_input("Font size", min_value=10, max_value=100, value=30)
margin_percent = st.number_input("Margin percentage", min_value=0, max_value=50, value=5)

if st.button("Generate Image"):
    # Convert color strings to RGB tuples
    start_rgb = tuple(int(start_color[1:][i:i+2], 16) for i in (0, 2, 4))
    end_rgb = tuple(int(end_color[1:][i:i+2], 16) for i in (0, 2, 4))

    # Generate image
    image = create_gradient_with_overlay_and_text(
        (width, height), start_rgb, end_rgb, 0.2, text, font_size, 1.5, margin_percent
    )

    # Display the image
    st.image(image, caption="Generated Gradient Image", use_column_width=True)

    # Convert image to base64 for preview
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()

    # Create download buttons
    st.download_button(
        label="Download Image",
        data=img_byte_arr,
        file_name="gradient_image.png",
        mime="image/png"
    )

    # Display base64 encoded image
    st.markdown(f"Base64 encoded image:")
    st.code(img_base64)