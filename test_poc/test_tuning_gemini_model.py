import os
import google.generativeai as genai
import json

GEMINI_MODEL = 'models/gemini-1.5-flash-latest'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
generation_config = {
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name=GEMINI_MODEL,
  generation_config=generation_config
)

# training  
training_data = [
  "input: cho xe: Raider 150 Kawasaki Z1000 Winner 150 CBR 150 GSX R150 GSX S150 Sonic 150 CB150R Satria F150 Winner X Yamaha R6- Nhớt Motul 7100 10W40 1L2 là loại nhớt mới tổng hợp hoàn toàn, phù hợp với các dòng xe số hiện đại trên thị trường Việt Nam với công Nghệ Ester cho ra hiệu suất tối đa dành cho các dòng xe thể thao chuyên về tốc độ.- API SP ; JASO MA2 - Độ nhớt 10W40 - Dung tích nhớt 1 lít 2 phù hợp tiện lợi cho các dòng xe Winner, Sonic, Satria...",
  "output: Nhớt Motul 7100 10W40 1L2",
  "input:  cho xe: Nhớt xe máy Air Blade SH Mode SH 125i/150i Lead PCX Nouvo Vespa Lx Elizabeth Click 125i/150i Dylan Ps Grande Air Blade 160 Vision Janus SH 160i Freego MioMotul Scooter Power LE 5W40 0.8L nhớt xe tay ga đời mới của tập đoàn nhớt Motul. Nhớt kiểm soát tốt cặn trong piston, chống mài mòn, chống ăn mòn cực kỳ hiệu quả với khả năng tẩy rửa tuyệt hảo giúp động cơ luôn được giữ sạch.- Dầu nhớt tổng hợp 100%.- Tiêu chuẩn: API SN, JASO MB.",
  "output: Nhớt Motul Scooter Power LE 5W40 0.8L",
  "input:  cho xe: Wave Dream Exciter 150 Exciter 135 Sirius Jupiter Axelo 125 Raider 150 Galaxy Future Exciter 155 Winner 150 MSX 125 CBR 150 Blade GSX R150 GSX S150 Sonic 150 R15 CB150R Husky Satria F150 Winner X Yamaha R6 XS155R Yamaha PG-1 Nhớt Motul 3100 Gold 4T 10W40 0,8L sử dụng cho các loại động cơ 4 thì của xe gắn máy đời mới, công suất mạnh chạy đường trường, địa hình… của các hãng như Honda, Yamaha, Suzuki, SYM …Motul 3100 Gold 10W40 là nhớt bán tổng hợp với khả năng chống oxy hoá tuyệt hảo, giúp kéo dài thời gian sử dụng.Tính năng bôi trơn cao giúp chống mài mòn, tăng cường tuổi thọ động cơ.Motul 3100 Gold 10W40 có tiêu chuẩn JASO MA2 giúp bộ ly hợp ướt hoạt động hiệu quả trong mọi điều kiện: khởi động, tăng tốc và tốc độ tối đa.",
  "output: Nhớt Motul 3100 Gold 4T 10W40 0,8L",
  "input:  cho xe: Wave Dream Sirius Jupiter Future CBR 150 Blade- Nhớt Motul Moto 20W50 là sản phẩm dầu nhớt động cơ dành cho các dòng xe gắn máy số 4 thì thông dụng vận hành trên các cung đường.- Sản phẩm với đặc tính bôi trơn tốt giúp giảm ma sát và mài mòn động cơ, bảo vệ bánh răng và ly hợp khi vận hành mỗi ngày. JASO MA2 giúp bộ ly hợp hoạt động hiệu quả khi khởi động, cũng như khi tăng tốc và đạt tốc độ tối đa. Dễ dàng sang số. Khả năng chống cắt và độ dày màng dầu tuyệt vời để bảo vệ bánh răng hộp số, giúp đảm bảo độ bền của động cơ.- Nhớt Motul Moto 20W50 1L dành cho các dòng xe số đã sử dụng lâu hoặc thường xuyên đi xa.",
  "output: Nhớt Motul Moto 20W50 1L",
  "input:  cho xe: Air Blade SH Mode SH 125i/150i Lead PCX Sirius Click 125i/150i Grande Air Blade 160 Vision Janus Vario 150/125 NVX SH 160i Freego Scoopy 110 Vario 160 Click 160 Mio- Motul Scooter Expert LE 10W30 0.8L nhớt chất lượng cho xe tay ga 4 thì đời mới như: AB, Vision, SH Mode, SHVN, Lead, Vario, Click... Giúp kiểm soát cặn piston, chống mài mòn hiệu quả giúp tăng tuổi thọ động cơ. Phù hợp với chế độ dừng chạy liên tục khi giao thông ở thành phố.- Dầu nhớt công nghệ bán tổng hợp.- Tiêu chuẩn: API SM, JASO MB.",
  "output: Nhớt Motul Scooter Expert LE 10W30 0.8L",
  "input: cho xe: Wave Dream Exciter 150 Exciter 135 Sirius Jupiter Axelo 125 Raider 150 Kawasaki Z1000 Future Exciter 155 Winner 150 MSX 125 CBR 150 Blade GSX R150 GSX S150 Sonic 150 R15 CB150R Husky Satria F150 Winner X Yamaha R6 XS155R Yamaha PG-1 Nhớt Fuchs Silkolene Pro 4 10W40 XP với đặc tính chạy êm mát máy, phù hợp với tất cả các loại xe số và xe tay côn hiện nay.- Dầu nhớt tổng hợp toàn phần 100% Full Synthetic- API SN, Jaso: MA2- Nhớt Fuchs Silkolene Pro 4 10W40 XP sản xuất tại Anh.",
  "output: Nhớt Fuchs Silkolene Pro 4 10W40 XP"
]

print("Bạn đang chạy xe gì ? ")
your_car = input()
training_data.append("input: các loại nhớt phù hợp cho xe " + your_car)
training_data.append("output: ")

response = model.generate_content(training_data)
print(response.text)