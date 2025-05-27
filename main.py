from flask import Flask, request, render_template, send_file
import pandas as pd
import os
import zipfile
from datetime import datetime
from unidecode import unidecode

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Hàm hỗ trợ
def assign_khoa(ma_nganh):
    if pd.isnull(ma_nganh):
        return None
    elif ('7480201' in ma_nganh or '7480103' in ma_nganh or '7480107' in ma_nganh):
        return 'Khoa Công nghệ thông tin'
    elif ('7510301' in ma_nganh or '7510205' in ma_nganh or '7510202' in ma_nganh or '7510103' in ma_nganh):
        return 'Khoa Kỹ thuật'
    elif ('7540101' in ma_nganh or '7510406' in ma_nganh or '7510401' in ma_nganh or '7420201' in ma_nganh or '7720301' in ma_nganh or '7720601' in ma_nganh):
        return 'Khoa Công nghệ'
    elif ('7320104' in ma_nganh or '7210403' in ma_nganh or '7210408' in ma_nganh):
        return 'Khoa Truyền thông - Thiết kế'
    elif ('7340101' in ma_nganh or '7810103' in ma_nganh or '7810201' in ma_nganh or '7510605' in ma_nganh):
        return 'Khoa Kinh tế quản trị'
    elif ('7340301' in ma_nganh or '7340201' in ma_nganh):
        return 'Khoa Kế toán - Tài chính'
    elif ('7220201' in ma_nganh or '7310608' in ma_nganh or '7220204' in ma_nganh):
        return 'Khoa Ngoại ngữ'
    else:
        return None

def remove_accent(text):
    if isinstance(text, str):
        return unidecode(text)
    return text

def unicode_hoten(df):
    hoten = (df['Họ'].apply(remove_accent) + ' ' + df['Tên'].apply(remove_accent) +
             ' ' + df['Điện Thoại'] +
             ' ' + df['Ngày Sinh'].str.replace(r'/', '', regex=True) +
             ' ' + 'XETHB2025')
    return hoten

def wrangling(file_path):
    # Đọc file Excel
    df = pd.read_excel(file_path, dtype=str)

    # Kiểm tra các cột bắt buộc
    required_columns = ['Họ', 'Tên', 'Điện Thoại', 'Số điện thoại phụ huynh', 
                        'Khu Vực theo THPT', 'Mã ngành_100', 'Mã ngành_200', 'Mã ngành_402']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Thiếu cột bắt buộc: {col}")
        
    # Chuẩn hóa cột Ngày đăng ký
    df['Ngày đăng ký'] = pd.to_datetime(df['Ngày đăng ký'], format='%d/%m/%Y', errors='coerce')
    if df['Ngày đăng ký'].isnull().any():
        raise ValueError("Cột 'Ngày đăng ký' chứa giá trị không hợp lệ hoặc bị thiếu.")

    # Chuẩn hóa dữ liệu
    df['Họ'] = df['Họ'].str.title()
    df['Tên'] = df['Tên'].str.title()
    df['diem_khuvuc'] = df['Khu Vực theo THPT'].apply({'KV 1': 0.75, 'KV 2-NT': 0.5, 'KV 2': 0.25}.get).fillna(0)
    df['Khoa_100'] = df['Mã ngành_100'].apply(assign_khoa)
    df['Khoa_200'] = df['Mã ngành_200'].apply(assign_khoa)
    df['Khoa_402'] = df['Mã ngành_402'].apply(assign_khoa)
    df['dien_thoai_HS'] = '84' + df['Điện Thoại'].str[1:]
    df['dien_thoai_PH'] = '84' + df['Số điện thoại phụ huynh'].str[1:]
    df['cu_phap_40k'] = unicode_hoten(df)
    return df

def thongke(df):
    # Thống kê theo ngày
    dangky_days = df.groupby('Ngày đăng ký').size().reset_index(name='Số lượng đăng ký')
    dangky_days = dangky_days.sort_values(by=['Ngày đăng ký'])  # Sắp xếp theo ngày tăng dần

    # Thống kê theo tuần
    df['Tuần'] = df['Ngày đăng ký'].dt.isocalendar().week
    dangky_tuan = df.groupby('Tuần').size().reset_index(name='Số lượng đăng ký')
    dangky_tuan = dangky_tuan.sort_values(by='Tuần')  # Sắp xếp theo tuần tăng dần

    # Thống kê theo tháng
    df['Tháng'] = df['Ngày đăng ký'].dt.month
    dangky_thang = df.groupby('Tháng').size().reset_index(name='Số lượng đăng ký')
    dangky_thang = dangky_thang.sort_values(by='Tháng')  # Sắp xếp theo tháng tăng dần

    return dangky_days, dangky_tuan, dangky_thang

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                # Lưu file tải lên và đổi tên
                now = datetime.now()
                time = now.strftime("%d%m%y")  # Định dạng ngày, tháng, năm
                file_extension = os.path.splitext(file.filename)[1]  # Lấy phần mở rộng file
                renamed_file = f'export-{time}{file_extension}'
                file_path = os.path.join(UPLOAD_FOLDER, renamed_file)
                file.save(file_path)

                # Xử lý file
                df = wrangling(file_path)

                # Xuất file CSV
                looker = df[['Số CMCD/CCCD', 'Giới Tính', 'Dân tộc', 'Khu Vực theo THPT',
                            'Tỉnh THPT', 'Trường THPT', 'Năm tốt nghiệp', 'Ngày đăng ký',
                            'Tên', 'Tên ngành_100', 'Tên ngành_200', 'Tên ngành_402',
                            'Khoa_100', 'Khoa_200', 'Khoa_402', 'dien_thoai_PH']]
                csv_path = os.path.join(OUTPUT_FOLDER, f'studio-looker-{time}.csv')
                looker.to_csv(csv_path, index=False, encoding='utf-8-sig')  # Đảm bảo không lỗi font

                # Thống kê theo ngày, tuần, tháng
                dangky_days, dangky_tuan, dangky_thang = thongke(df)

                # Xuất file Excel thống kê
                excel_path = os.path.join(OUTPUT_FOLDER, f'TK-DWM-{time}.xlsx')
                with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                    dangky_days.to_excel(writer, sheet_name='Tk Theo ngày', index=False)
                    dangky_tuan.to_excel(writer, sheet_name='Tk Theo tuần', index=False)
                    dangky_thang.to_excel(writer, sheet_name='Tk Theo tháng', index=False)

                # Nén các file thành file .zip với tên theo ngày, tháng, năm
                zip_path = os.path.join(OUTPUT_FOLDER, f'{time}.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    zipf.write(file_path, os.path.basename(file_path))  # Thêm file gốc
                    zipf.write(csv_path, os.path.basename(csv_path))    # Thêm file CSV
                    zipf.write(excel_path, os.path.basename(excel_path))  # Thêm file Excel thống kê

                return render_template('index.html', success=True, download_link=zip_path)

            except Exception as e:
                return render_template('index.html', success=False, error=str(e))
    return render_template('index.html', success=None)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)